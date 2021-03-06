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


def process_bridge(uploader):
    '''
    Same functionality as read_bridge_deprecated, but added with column identification features
    
    * 2.2 : dropna() 
    * 2.3 : removed trailing/leading whitespace in whoart column by clean_list() (LLT column unnecessary due to automatic identification as float)
    * 3.0 : removed mode parameter since only mode 1 processes bridge now (no need to branch paths)
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



def connect(source, meddra, source_cols, mode, filename, how="left"):
    '''
    New version of generate_full_bridge_deprecated that can be used for AE list extension as well as classic bridge extension
    
    bridge : series or dataframe that is to be extended
    bridge_cols=[_, <exact LLT code column name in bridge>]
    spl : SOC, PT, LLT terms from MedDRA source file
    how="left" : left join to align with input bridge file
    
    Assumes MedDRA columns do not change in the future
    
    * 2.1 : Removed drop duplicate; Dropped duplicate column later (at the end)
    * 3.0 : mode 2 deprecated 
    '''

    if mode == "1":
        extended = pd.merge(source, meddra, how=how, left_on=source_cols[1], right_on="llt_code")
    else:
        if isinstance(source, pd.DataFrame):
            extended = pd.merge(source, meddra, how=how, left_on=source_cols[1], right_on="llt_name")
        else:
            extended = pd.merge(source.to_frame(name="llt_name"), meddra, how=how, on="llt_name")

    
    if extended.isna().any().any():
        print("*" * 40)
        missing = extended.loc[extended.isna().any(axis=1)][source_cols[1]].values
        print("{}??? ???????????? LLT code:".format(filename))
        for m in missing:
            print("    {}".format(m))
        print("??? LLT code??? MedDRA folder (llt.asc / mdhier.asc)??? ????????????. MedDRA folder (llt.asc / mdhier.asc) ???????????? ???????????????.")
        print("  * ?????? ??????: AE list ????????? ??? LLT code (????????? ??? LLT code??? ????????? WHOART ?????? 1) ???????????? ????????? ???????????????".format(missing))

        print("    (0) ??????")
        print("    (1) NaN?????? ??????")
        print("    (2) NaN ??????")
        num = input(": ")

        while num not in ["0" , "1", "2"]:
            print("    (0) ??????")
            print("    (1) NaN?????? ??????")
            print("    (2) NaN ??????")
            num = input("0/1/2 ???????????????: ")

        if num == "0":
            raise utility.StopExecution
        elif num == "1":
            # keep
            pass
        else:
            extended = extended.dropna().reset_index(drop=True)
        
    if isinstance(source, pd.DataFrame):
        extended = extended.drop(columns=[source_cols[1]])
        
    return extended


def process_ae(uploader, mode):
    '''
    Processes AE list 
    Returns  
    - AE list dataframe with case number (or row number if not present)
    - List of column names [case number (or row number), term]
    
    * 1.2 : dropna()
    * 1.3 : removed trailing/leading whitespace for whoart column by clean_list()
    * 2.0 : only mode 2 processes AE list now (no need to branch paths)
    * 2.1 : updated with new functionalities (e.g., clean list value, remove rows with empty string)
    '''
    uploader = uploader.value
    file_name = list(uploader.keys())[0]
    df = pd.read_excel(io.BytesIO(uploader[file_name]["content"]))
    
    # Drop empty rows at end, if any
    df = df[df.columns].dropna(how="all")
    
    # remove leading/trailing whitespace in column names
    df.columns = utility.clean_list(df.columns)
    
    cols = utility.ae_identify(df.columns, mode)
    
    while df[cols[1]].isna().any():
        # If any are NaN values in significant column, reselect
        print("{}????????? ??????????????????. ?????? ???????????????.".format(cols[1]))
        subset = list(df.columns)
        subset.remove(cols[1])
        cols = utility.ae_identify(subset, mode)
    
    try:
        # Signficiant column is LLT term or WHO-ART (str), so no type error
        df[cols[1]] = utility.clean_list(list(df[cols[1]])) 
    except AttributeError:
        print("AE list ?????? ????????? ????????? ??????.")
        print("??????.")
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
    Mode 1 issue only
    Solves duplicate WHOART terms in bridge file
    '''
    
    print("*" * 40)
    print("WHOART-MEDDRA bridge??? ?????? WHOART ??????1??? ?????? LLT/SOC??? ???????????????")
    print("    (1) ?????? LLT/SOC ??? ??????")
    print("    (2) ?????? ??????")
    print("    (3) ????????? LLT/SOC ??????")
    print("    (4) ??????")
    option = input("Duplicate ?????? ??????: ")
    
    while option not in ["1", "2", "3", "4"]:
        option = input("?????? ???????????????: ")

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
                num = input("'{}' ?????? ??????????????? (?????? ??????): ".format(s))

                while not num.isdigit() or not int(num) < len(partial_df):
                    num = input("'{}' ?????? ?????? ??????????????? (?????? ??????): ".format(s))

                rows.append(partial_df.iloc[int(num)])

            unique_df = pd.DataFrame(rows, columns=full_bridge.columns)
            return pd.concat([removed_duplicates_df, unique_df], ignore_index=True)
        
        
        # Option 3
        # Select all the duplicated terms
        filtered_dup = filtered.loc[filtered.duplicated(subset=["??????1"], keep=False)]
        
        # Select the first occurence of all duplicated terms (read duplicated docs)
        first_unique_df = filtered_dup.loc[~filtered_dup.duplicated(subset=["??????1"], keep="first")].reset_index(drop=True)
        
        return pd.concat([removed_duplicates_df, first_unique_df], ignore_index=True)
            
    else:
        raise utility.StopExecution
    
    
    
def index_ae_list(ae_list, full_key, whoart, how="left"):
    '''
    Used exclusively for mode 1
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
            print("AE list??? ?????? WHOART ??????1 {} ??? WHOART-MEDDRA bridge file??? ????????????. WHOART-MEDDRA bridge file??? ???????????? ?????????.".format(missing))
            print("    (0) ??????")
            print("    (1) NaN?????? ??????")
            print("    (2) NaN ??????")
            num = input(": ")

            while num != "0" and num != "1" and num != "2":
                print("    (0) ??????")
                print("    (1) NaN?????? ??????")
                print("    (2) NaN ??????")
                num = input("0, 1, 2 ???????????????: ")

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

def make_meddra_unique(meddra):
    '''
    New function added with mode 1, 2 update
    Removes duplicates in MedDRA joined dataframe where every other column except llt_code is the same
    - Different with each language
    '''
    repeats = meddra.loc[meddra.duplicated(subset=["llt_name", "pt_code", "soc_code", "soc_name"], keep=False)]
    unique = repeats.loc[~repeats.duplicated(subset=["llt_name", "pt_code", "soc_code", "soc_name"], keep="first")].sort_index()
    rest = meddra.loc[~meddra.duplicated(subset=["llt_name", "pt_code", "soc_code", "soc_name"], keep=False)]
    return pd.concat([rest, unique], sort=False).sort_index().reset_index(drop=True)



def prompt_modes():
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


def control_process(items, mode):
    '''
    Program main function
    
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
    meddra_uniq = make_meddra_unique(meddra)

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
    full_ae_list = full_ae_list.drop(columns=["llt_code", "pt_code", "soc_code"])
    full_ae_list = full_ae_list.rename(columns={'llt_name' : 'MedDRA LLT',
                                                'pt_name' : "MedDRA PT",
                                                'soc_name' : "MedDRA SOC"})
    return full_ae_list