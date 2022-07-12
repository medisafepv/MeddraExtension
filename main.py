import io
import pandas as pd
import ipywidgets as widgets
from ipywidgets import HBox, FileUpload, Layout

import utility

def process_llt(uploaded):
    llt_names = ["llt_code", "llt_name", "pt_code",
             "llt_soc_code", "llt_whoart_code", "llt_harts_code",
             "llt_costart_sym", "llt_icd9_code", "llt_icd10_code",
             "llt_jart_code", "t1", "t2"]

    return utility.read_meddra_files(uploaded, llt_names, ["llt_code", "llt_name", "pt_code"])


def process_hierarchical(uploaded):
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
    spl = pd.merge(hier, llt, how=how, on=on)
    assert not spl.isna().any().any()
    return spl


def process_bridge(uploader, mode):
    '''
    Same functionality as read_bridge_deprecated, but added with column identification features
    
    * 2.2 : dropna() 
    * 2.3 : removed trailing/leading whitespace in whoart column by clean_list() (LLT column unnecessary due to automatic identification as float)
    '''
    uploader = uploader.value
    file_name = list(uploader.keys())[0]
    bridge = pd.read_excel(io.BytesIO(uploader[file_name]["content"]))
    
    bridge.columns = utility.clean_list(bridge.columns)
    
    cols = utility.bridge_identify(bridge.columns, mode)
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


def connect(bridge, spl, bridge_cols, mode, filename, how="left"):
    '''
    New version of generate_full_bridge_deprecated that can be used for AE list extension as well as classic bridge extension
    
    bridge : series or dataframe that must contain LLT code
    bridge_cols=[_, <exact LLT code column name in bridge>]
    spl : SOC, PT, LLT terms from MedDRA source file
    how="left" : left join to align with input bridge file
    
    Assumes MedDRA columns do not change in the future
    
    *2.1 : Removed drop duplicate; Dropped duplicate column later (at the end)
    '''

    if isinstance(bridge, pd.DataFrame):
        extended = pd.merge(bridge, spl, how=how, left_on=bridge_cols[1], right_on="llt_code")
    else:
        extended = pd.merge(bridge.to_frame(name="llt_code"), spl, how=how, on="llt_code")
    
    if extended.isna().any().any():
        print("*" * 40)
        missing = extended.loc[extended.isna().any(axis=1)][bridge_cols[1]].values
        print("{}에 있는 LLT code {}가 MedDRA folder (llt.asc / mdhier.asc)에 없습니다. MedDRA folder (llt.asc / mdhier.asc)가 최신 버전인지 확인하세요.".format(filename, missing))
        print("  *참고 노트: AE list 파일에 LLT code {} (또는 매칭 된 WHOART 용어1)가 없으면 문제가 발생하지 않습니다; 이 경우에는 (1 or 2) 선택하세요.".format(missing))
        print("  *참고 노트: AE list 파일에 LLT code {} (또는 매칭 된 WHOART 용어1)가 있으면 문제가 발생합니다; 이 경우에는 (0) 선택하시고, MedDRA folder (llt.asc / mdhier.asc)가 최신 버전인지 확인하세요.".format(missing))

        print("    (0) 종료")
        print("    (1) NaN으로 진행")
        print("    (2) NaN 삭제")
        num = input(": ")

        while num != "0" and num != "1" and num != "2":
            print("    (0) 종료")
            print("    (1) NaN으로 진행")
            print("    (2) NaN 삭제")
            num = input("0/1/2 입력해주세요: ")

        if num == "0":
            raise utility.StopExecution
        elif num == "1":
            # keep
            pass
        else:
            extended = extended.dropna().reset_index(drop=True)
        
    if isinstance(bridge, pd.DataFrame):
        # Merging during bridge extension produces duplicate MedDRA LLT code columns. Keep the MedDRA source column.
        extended = extended.drop(columns=[bridge_cols[1]])
        
    return extended


def process_ae(uploader, mode):
    '''
    
    
    * 1.2 : dropna()
    * 1.3 : removed trailing/leading whitespace for whoart column by clean_list()
    '''
    uploader = uploader.value
    file_name = list(uploader.keys())[0]
    df = pd.read_excel(io.BytesIO(uploader[file_name]["content"]))
    
    # remove leading/trailing whitespace in column names
    df.columns = utility.clean_list(df.columns)
    
    cols = utility.ae_identify(df.columns, mode)
    
    while not (~df[cols[1]].isna()).any():
        # If ALL are NaN values, reselect
        print("{}컬럼이 비어있습니다. 다시 선택해주세요.".format(cols[1]))
        subset = list(df.columns)
        subset.remove(cols[1])
        cols = utility.ae_identify(subset, mode)
    
    try:
        df[cols[1]] = utility.clean_list(df[cols[1]]) # will result in error if LLT
    except TypeError:
        pass
    
    if "" in cols:
        # If missing a column, there can only be missing case no. due to invariant of ae_identify() => cols[1]
        df = df.reset_index().rename(columns={"index" : "Row Number"})
        
        df["Row Number"] = df["Row Number"] + 2 
        # Add header and convert to 1-indexing
        
        new_cols = ["Row Number", cols[1]]
        return df[new_cols].dropna(how="all", subset=[cols[1]]), new_cols
    else:
        return df[cols].dropna(how="all", subset=cols), cols
    
    
def solve_duplicates(full_bridge, ae_list, fb_whoart, ae_whoart):
    '''
    Mode 1 issue only
    Solves duplicate WHOART terms in bridge file
    '''
    
    print("*" * 40)
    print("WHOART-MEDDRA bridge에 같은 WHOART 용어1로 다른 LLT/SOC을 찾았습니다")
    print("    (1) 여러 LLT/SOC 다 포함")
    print("    (2) 직접 선택")
    print("    (3) 첫번제 LLT/SOC 선택")
    print("    (4) 종료")
    option = input("Duplicate 처리 방법: ")
    
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
            for s in whoart_set:
                partial_df = full_bridge.loc[full_bridge[fb_whoart] == s].reset_index(drop=True)
                print(partial_df.to_string())
                num = input("'{}' 행을 선택하세요 (왼쪽 숫자): ".format(s))

                while not num.isdigit() or not int(num) < len(partial_df):
                    num = input("'{}' 행을 다시 선택하세요 (왼쪽 숫자): ".format(s))

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
    
    '''
    terms = ["llt_name", "pt_name", "soc_name"]
    interested = list(ae_list.columns) + terms
    
    combined = pd.merge(left=ae_list, right=full_key, how="left", left_on=ae_list.columns[1], right_on=whoart)
    
    combined = combined[interested]
    
    
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
                num = input("0/1/2 입력해주세요: ")

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
    uploader = FileUpload(description=description, layout=Layout(width="250px"), multiple=False)
    display(uploader)

    main_display = widgets.Output()

    def on_upload_change(inputs):
        with main_display:
            main_display.clear_output()
            display(list(inputs['new'].keys())[-1])

    uploader.observe(on_upload_change, names='value')
    return uploader


def prompt_modes():
    utility.print_modes()
    mode = input("Select program modes: ")
    while mode != "1" and mode != "2" and mode != "3" and mode != "4":
        utility.print_modes()
        mode = input("Select program modes: ")

    if mode == "4":
        raise utility.StopExecution

    words = {"1" : ["llt.asc", "mdhier.asc", "WHOART-MedDRA bridge.xlsx", "AE list"], 
             "2" : ["llt.asc", "mdhier.asc", "WHOART-MedDRA bridge.xlsx"], 
             "3" : ["llt.asc", "mdhier.asc", "AE list"]}

    items = []
    for w in words[mode]:
        items.append(prompt_upload(description=w))
        
    return items, mode


def control_process(items, mode):
    '''
    items[0] : llt.asc
    items[1] : mdhier.asc
    items[2] : bridge.xlsx, if mode 1 or 2
    items[2] : AE list.xlsx, if mode 3
    items[3] : AE list.xlsx, if mode 1
    '''

    # Required for all modes
    llt = process_llt(items[0])
    soc_pt = process_hierarchical(items[1])
    meddra = merge_soc_pt_llt(llt, soc_pt)

    if mode != "3":
        # Modes 1 and 2 take bridge file as input
        partial_bridge, bridge_columns = process_bridge(items[2], mode)
        full_bridge = connect(partial_bridge, meddra, bridge_columns, mode, filename="WHO-ART MedDRA bridge")

        if mode == "2" or not isinstance(partial_bridge, pd.DataFrame):
            # Bridge extension mode
            full_bridge = full_bridge.drop(columns=["pt_code", "soc_code"])
            full_bridge = full_bridge.rename(columns={"llt_code" : 'MedDRA LLT Code', 'llt_name' : 'MedDRA LLT', 'pt_name' : "MedDRA PT", 'soc_name' : "MedDRA SOC"})
            return full_bridge

        # Modes 1 takes AE list as input
        if mode == "1":
            ae_list, ae_list_columns = process_ae(items[3], mode)
            
            # Handle duplicates
            full_bridge = solve_duplicates(full_bridge, ae_list, bridge_columns[0], ae_list_columns[1])
            
            indexed = index_ae_list(ae_list, full_bridge, bridge_columns[0])
            return indexed
    
    # Modes 3 takes AE list as input
    ae_list, ae_list_columns = process_ae(items[2], mode)
    full_ae_list = connect(ae_list, meddra, ae_list_columns, mode, filename="AE list")
    full_ae_list = full_ae_list.drop(columns=["pt_code", "soc_code"])
    full_ae_list = full_ae_list.rename(columns={"llt_code" : 'MedDRA LLT Code','llt_name' : 'MedDRA LLT','pt_name' : "MedDRA PT", 'soc_name' : "MedDRA SOC"})
    final = full_ae_list