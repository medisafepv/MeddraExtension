'''
final_WM program

Author: Sion Kim
Contact: sionkim@umich.edu
Latest Edit: 07/29/2022
'''

# Libraries
import io
import pandas as pd
import difflib
import ipywidgets as widgets
from ipywidgets import HBox, FileUpload, Layout

# Helper functions
import utility

def process_llt(uploaded):
    '''
    Given uploaded llt.asc file, returns a dataframe with the columns ["llt_code", "llt_name", "pt_code"] only
    - uploaded : FileUpload instance from ipywidget class (contains necessary file)
    '''
    llt_names = ["llt_code", "llt_name", "pt_code",
             "llt_soc_code", "llt_whoart_code", "llt_harts_code",
             "llt_costart_sym", "llt_icd9_code", "llt_icd10_code",
             "llt_jart_code", "t1", "t2"]

    return utility.read_meddra_files(uploaded, llt_names, ["llt_code", "llt_name", "pt_code"])


def process_hierarchical(uploaded):
    '''
    Given uploaded mdhier.asc file, returns a dataframe with the columns ["pt_code", "pt_name", "soc_code", "soc_name"] only
    Note: 
        In case of multiple PT/SOC branches for one LLT, the primary PT/SOC terms will be used. 
        Functionality to allow secondary terms has not been implemented, but may be necessary in the future
    
    - uploaded : FileUpload instance from ipywidget class (contains necessary file)
    '''
    hier_names = ["pt_code", "hlt_code", "hlgt_code",
                             "soc_code", "pt_name", "hlt_name",
                             "hlgt_name", "soc_name", "soc_abbrev", "null_field",
                             "pt_soc_code", "primary_soc_fg", "t1", "t2"]

    hier = utility.read_meddra_files(uploaded, hier_names, ["pt_code", "pt_name",
                                               "soc_code", "soc_name",
                                               "primary_soc_fg"])
    hier = hier.loc[hier["primary_soc_fg"] != 'N']
    hier = hier[["pt_code", "pt_name", "soc_code", "soc_name"]]
    return hier

def merge_soc_pt_llt(hier, llt, how="inner", on="pt_code"):
    '''
    Joins the llt.asc and mdhier.asc files by an inner join on 'pt_code' keyword
    Follows the join table diagram in 'intguide_ 25_0_English.pdf' file located in MedDRA_25_0_English folder
    
    '''
    spl = pd.merge(hier, llt, how=how, on=on)
    assert not spl.isna().any().any()
    return spl


def process_bridge(uploader):
    '''
    Given uploaded WHOART-MEDDRA file, returns 
    1. dataframe with the columns [<WHOART column>, <LLT Code column>] only
    2. columns [<WHOART column>, <LLT Code column>]
        columns is returned due to an instance in which column titles in dataframe were switched (i.e., unable to identify which is WHOAT and LLT).
        May not be needed if column order invariance is guaranteed by pandas
        
    - uploaded : FileUpload instance from ipywidget class (contains necessary file)
    
    Old notes:
    Same functionality as read_bridge_deprecated, but added with column identification features
    
    * 2.2 : dropna() 
    * 2.3 : removed trailing/leading whitespace in whoart column by clean_list() (LLT column unnecessary due to automatic identification as float)
    * 3.0 : removed mode parameter since only mode 1 processes bridge now (i.e., no need to branch paths)
    '''
    uploader = uploader.value
    file_name = list(uploader.keys())[0]
    bridge = pd.read_excel(io.BytesIO(uploader[file_name]["content"]))
    
    bridge.columns = utility.clean_list(bridge.columns)
    
    cols = utility.bridge_identify(bridge.columns)
    interested = list()
    for c in cols:
        if c:
            interested.append(c)
    
    
    if len(interested) == 1:
        # no whoart column
        return bridge[interested[0]].dropna(how="all"), cols
    else:
        # whoart AND LLT column
        
        bridge = bridge[interested].dropna(how="all", subset=interested)
        
        # clean whoart column
        bridge[interested[0]] = utility.clean_list(bridge[interested[0]])
        
        return bridge, cols

    


def connect(source, meddra, source_cols, mode, filename, how="left", first_call=True):
    '''
    Used to extend AE list (mode 2) and bridge (mode 1)
    
    source : series or dataframe that is to be extended
    source_cols = [_, <exact LLT column name in source>]
    meddra : SOC, PT, LLT terms from MedDRA source file
    how = "left" : left join to align with input source file
        
    * 2.1 : Removed drop duplicate; Dropped duplicate column later (at the end)
    * 3.0 : Mode 3 deprecated 
    * 4.0 : Similar match functionality and lower case standardization for indexing
    * 4.1 : Customize max number of similarity matches
    * 4.2 : Changed first_call behaviour
    * 5.0 : Ability to reset parameters midloop
    * 5.1 : Infinite loop fixed (when no search results found)
    '''

    if mode == "1":
        extended = pd.merge(source, meddra, how=how, left_on=source_cols[1], right_on="llt_code")
    else:
        if isinstance(source, pd.DataFrame):
            extended = pd.merge(source, meddra, how=how, left_on=source_cols[1], right_on="llt_name_lc")
        else:
            extended = pd.merge(source.to_frame(name="llt_name_lc"), meddra, how=how, on="llt_name_lc")

    if extended.isna().any().any():
        print("*" * 40)
        missing = extended.loc[extended.isna().any(axis=1)][source_cols[1]].values
        print("{}에 해당하는 LLT:".format(filename))
        for m in missing:
            print("    {}".format(m))
            
        print("위 LLT는 MedDRA folder (llt.asc / mdhier.asc)에 없습니다.")
        
        if len(missing) == len(source):
            print("**'{}'의 언어와 llt.asc / mdhier.asc의 언어가 같은지 확인**".format(source_cols[1]))
        
        if mode == "1":
            print("**위에 출력된 LLT (정확히 LLT랑 매칭하는 WHOART 용어 1)이 AE list 파일에 해당해야 문제가 발생합니다**".format(missing))
            print("**AE list 파일에 출력된 LLT가 없는지 확인 후, 옵션 (2)/(3)로 진행하세요. 그 외에는 (1)로 직접 선택하세요.**")
        
        print("    (0) 종료")
        print("    (1) 비슷한 용어 찾고 직접 선택")
        print("    (2) NaN으로 진행")
        print("    (3) NaN 삭제")
        num = input(": ")

        while num not in ["0" , "1", "2", "3"]:
            num = input("(0, 1, 2, 3) 입력하세요: ")

        if num == "0":
            raise utility.StopExecution
        elif num == "1":
            # Set initial search parameters
            eps, N = utility.prompt_search_parameters()
            
            # Loop through all unrecognized words
            for word_num, m in enumerate(missing):
                matches = []
                opt = "0"
                
                while int(opt) == len(matches):
                    
                    if int(opt) > 0:
                        # Selected to reset parameters
                        eps, N = utility.prompt_search_parameters()
                
                    # Otherwise, continue with past set values
                    print("({}/{}) MedDRA folder에 '{}'랑 비슷한 용어 찾는중...".format(word_num + 1, len(missing), m), end="")
                    matches = difflib.get_close_matches(m, meddra["llt_name_lc"], n=int(N), cutoff=float(eps))

                    if matches:
                        print()
                        for i, sim in enumerate(matches):
                            print("    ({}) {}".format(i, sim))

                        print("    ({}) 설정 다시선택하기 (검색 범위 확장)".format(len(matches)))
                              
                        opt = input("  '{}' ≈ ".format(m))
                        while not opt.isdigit() or int(opt) > len(matches):
                            opt = input("  '{}' ≈ ".format(m))
                            
                        if int(opt) == len(matches):
                            continue

                        source.loc[source[source_cols[1]] == m, source_cols[1]] = matches[int(opt)]
                    else:
                        print("검색 결과 없음.")
                        break

            extended = connect(source, meddra, source_cols, mode, filename, how, first_call=False)

        elif num == "2":
            pass # as is
        else:
            extended = extended.dropna().reset_index(drop=True)

        
    if first_call and isinstance(source, pd.DataFrame):
        extended = extended.drop(columns=[source_cols[1]])
        
    return extended


def process_ae(uploader, mode):
    '''
    Processes AE list 
    Returns  
    1. AE list dataframe with case number (or row number if not present)
    2. List of column names [case number (or row number), term]
    
    * 1.2 : dropna()
    * 1.3 : removed trailing/leading whitespace for whoart column by clean_list()
    * 2.0 : only mode 2 processes AE list now (no need to branch paths)
    * 2.1 : updated with new functionalities (e.g., clean list value, remove rows with empty string)
    * 2.2 : LLT lowercase standardization for indexing
    * 2.3 : remove rows if LLT or WHOART column is missing any values
    '''
    uploader = uploader.value
    file_name = list(uploader.keys())[0]
    df = pd.read_excel(io.BytesIO(uploader[file_name]["content"]))
    
    # Drop empty rows at end, if any
    df = df.dropna(how="all")
    
    # remove leading/trailing whitespace in column names
    df.columns = utility.clean_list(df.columns)
    
    # cols[1] is LLT or WHOART column
    cols = utility.ae_identify(df.columns, mode)
    
    while df[cols[1]].isna().all():
        # If all are NaN values in significant column, reselect
        print("{}컬럼이 비어있습니다. 다시 선택하세요.".format(cols[1]))
        subset = list(df.columns)
        subset.remove(cols[1])
        cols = utility.ae_identify(subset, mode)
    
    # Guaranteed that LLT or WHOART column has SOME value
    df = df.dropna(subset=[cols[1]])
    
    try:
        # Signficiant column is LLT term or WHO-ART (str), so no type error
        df[cols[1]] = utility.clean_list(list(df[cols[1]]))
        
        # Make lowercase
        df[cols[1]] = df[cols[1]].str.lower()
        
    except AttributeError:
        print("AE list 파일 컬럼이 숫자로 인식.")
        print("종료.")
        raise utility.StopExecution

    # Remove rows with empty string, if exists after cleaning
    df = df[df[cols[1]].astype(bool)] 
    
    if "" in cols:
        # If missing a column, there can only be missing case no. due to invariant of ae_identify() => cols[1]
        df = df.reset_index().rename(columns={"index" : "Row Number"})
        
        df["Row Number"] = df["Row Number"] + 2 
        # Add header and convert to 1-indexing
        
        new_cols = ["Row Number", cols[1]]
        
        return df[new_cols], new_cols
    else:
        return df[cols], cols
    
    
def solve_duplicates(full_bridge, ae_list, fb_whoart, ae_whoart):
    '''
    Mode 1 only
    Solves duplicate WHOART terms in bridge file
    
    * 1.1 : Added progress counter
    '''
    
    print("*" * 40)
    print("WHOART-MEDDRA bridge에 같은 WHOART 용어1로 다른 LLT/SOC을 찾았습니다")
    print("    (1) 여러 LLT/SOC 다 포함")
    print("    (2) 직접 선택")
    print("    (3) 첫번제 LLT/SOC 선택")
    print("    (4) 종료")
    option = input("처리 방법: ")
    
    while option not in ["1", "2", "3", "4"]:
        option = input("다시 선택하세요: ")

    if option == "1":
        return full_bridge
    elif option == "2" or option == "3":
        # Remove all duplicates from full_bridge (to be combined later)
        removed_duplicates_df = full_bridge.drop_duplicates(subset=[fb_whoart], keep=False)
        
        # Filter whoart terms that are present in `ae_list` from `full_bridge` (i.e., we only care about whoart terms in ae_list)
        filtered = full_bridge.loc[full_bridge[fb_whoart].isin(list(ae_list[ae_whoart]))].reset_index(drop=True)
        
        if option == "2":
            # Make a unique list of repeated whoart terms
            whoart_set = pd.unique(filtered.loc[filtered.duplicated(subset=[fb_whoart], keep=False)].reset_index(drop=True)[fb_whoart])
            
            # Manually select
            rows = list()
            for i, s in enumerate(whoart_set):
                partial_df = full_bridge.loc[full_bridge[fb_whoart] == s].reset_index(drop=True)
                print(partial_df.to_string())
                num = input("({}/{}) '{}' 행을 선택하세요 (왼쪽 숫자): ".format(i + 1, len(whoart_set), s))

                while not num.isdigit() or not int(num) < len(partial_df):
                    num = input("({}/{}) '{}' 행을 다시 선택하세요 (왼쪽 숫자): ".format(i + 1, len(whoart_set), s))

                rows.append(partial_df.iloc[int(num)])

            unique_df = pd.DataFrame(rows, columns=full_bridge.columns)
            return pd.concat([removed_duplicates_df, unique_df], ignore_index=True)
        
        
        # Option 3
        # Select all the duplicated terms
        filtered_dup = filtered.loc[filtered.duplicated(subset=["용어1"], keep=False)]
        
        # Select the first occurence of all duplicated terms (read duplicated docs)
        first_unique_df = filtered_dup.loc[~filtered_dup.duplicated(subset=["용어1"], keep="first")].reset_index(drop=True)
        
        return pd.concat([removed_duplicates_df, first_unique_df], ignore_index=True)
            
    else:
        raise utility.StopExecution
    
    
    
def index_ae_list(ae_list, full_key, whoart, how="left"):
    '''
    Mode 1 only
    Conducts a left join on AE list and the WHOART-MEDDRA dataframe which also contains corresponding PT/SOC tterms
    
    - whoart : string title for the WHOART column in WHOART-MEDDRA dataframe
    '''
    terms = ["llt_name", "pt_name", "soc_name"]
    interested = list(ae_list.columns) + terms
    
    combined = pd.merge(left=ae_list, right=full_key, how="left", left_on=ae_list.columns[1], right_on=whoart)
    
    combined = combined[interested]
    
    # Exception handling
    if combined.isna().any().any():
        # There is any missing value 
        print("*" * 40)
        if combined.isna().any()["llt_name"]:
            # If bridge file is missing necessary whoart terms
            
            missing = combined.loc[combined.isna().any(axis=1)][ae_list.columns[1]].values
            print("AE list에 있는 WHOART 용어1 {} 이 WHOART-MEDDRA bridge file에 없습니다. WHOART-MEDDRA bridge file을 업데이트 하세요.".format(missing))
            print("    (0) 종료")
            print("    (1) NaN으로 진행")
            print("    (2) NaN 삭제")
            num = input(": ")

            while num != "0" and num != "1" and num != "2":
                print("    (0) 종료")
                print("    (1) NaN으로 진행")
                print("    (2) NaN 삭제")
                num = input("0, 1, 2 입력하세요: ")

            if num == "0":
                raise utility.StopExecution
            elif num == "1":
                # keep
                pass
            else:
                combined = combined.dropna().reset_index(drop=True)
    
    # Rename last three columns
    combined.columns = list(ae_list.columns) + ["MedDRA LLT", "MedDRA PT", "MedDRA SOC"]
    
    return combined

def prompt_upload(description):
    '''
    Prompts use to upload a file by ipywidget. Returns instance of FileUpload. 
    - description : string desciption for file upload widget
    '''
    uploader = FileUpload(description=description, layout=Layout(width="250px"), multiple=False)
    display(uploader)

    main_display = widgets.Output()

    def on_upload_change(inputs):
        with main_display:
            main_display.clear_output()
            display(list(inputs['new'].keys())[-1])

    uploader.observe(on_upload_change, names='value')
    return uploader

def make_meddra_unique(meddra):
    '''
    Removes duplicates in MedDRA joined dataframe where every other column except llt_code is the same
        Different behaviour for different languages
    '''
    repeats = meddra.loc[meddra.duplicated(subset=["llt_name", "pt_code", "soc_code", "soc_name"], keep=False)]
    unique = repeats.loc[~repeats.duplicated(subset=["llt_name", "pt_code", "soc_code", "soc_name"], keep="first")].sort_index()
    rest = meddra.loc[~meddra.duplicated(subset=["llt_name", "pt_code", "soc_code", "soc_name"], keep=False)]
    return pd.concat([rest, unique], sort=False).sort_index().reset_index(drop=True)



def prompt_modes():
    '''
    Prompts user for mode (1/2) and prompts the corresponding files
    '''
    utility.print_modes()
    mode = input("Select program modes: ")
    while mode not in ["1", "2", "3"]:
        utility.print_modes()
        mode = input("Reselect program modes (1, 2, 3): ")

    if mode == "3":
        raise utility.StopExecution

    words = {"1" : ["llt.asc", "mdhier.asc", "WHOART-MedDRA bridge (.xlsx)", "AE list (.xlsx)"], 
         "2" : ["llt.asc", "mdhier.asc", "AE list (.xlsx)"]}

    items = []
    for w in words[mode]:
        items.append(prompt_upload(description=w))
        
    return items, mode


def add_lowercase_col(meddra):
    '''
    Adds a column titled 'llt_name_lc' that is an exact copy of 'llt_name' but lowercase
    '''
    meddra["llt_name_lc"] = meddra["llt_name"].str.lower()
    return meddra


def control_process(items, mode):
    '''
    main function
    
    items[0] : llt.asc
    items[1] : mdhier.asc
    items[2] : bridge.xlsx, if mode 1
    items[2] : AE list.xlsx, if mode 2
    items[3] : AE list.xlsx, if mode 1
    '''

    # Required for all modes
    llt = process_llt(items[0])
    soc_pt = process_hierarchical(items[1])
    meddra = merge_soc_pt_llt(llt, soc_pt)
    meddra_uniq = add_lowercase_col(make_meddra_unique(meddra))

    if mode == "1":
        # Only mode 1 takes bridge file as input
        partial_bridge, bridge_columns = process_bridge(items[2])

        # When forming the full bridge (i.e., all MedDRA terms), include all llt codes 
        full_bridge = connect(partial_bridge, meddra, bridge_columns, mode, filename="WHOART MedDRA bridge")

        ae_list, ae_list_columns = process_ae(items[3], mode)

        # Handle duplicates
        full_bridge = solve_duplicates(full_bridge, ae_list, bridge_columns[0], ae_list_columns[1])

        indexed = index_ae_list(ae_list, full_bridge, bridge_columns[0])
        return indexed

    # Mode 2 takes AE list as input
    ae_list, ae_list_columns = process_ae(items[2], mode)
    full_ae_list = connect(ae_list, meddra_uniq, ae_list_columns, mode, filename="AE list")
    full_ae_list = full_ae_list.drop(columns=["llt_code", "pt_code", "soc_code", "llt_name_lc"])
    full_ae_list = full_ae_list.rename(columns={'llt_name' : 'MedDRA LLT',
                                                'pt_name' : "MedDRA PT",
                                                'soc_name' : "MedDRA SOC"})
    return full_ae_list


