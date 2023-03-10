'''
final_WM program

Author: Sion Kim
Contact: sionkim@umich.edu
Latest Edit: 07/29/2022
'''

# Libraries
import io
import pandas as pd


class StopExecution(Exception):
    '''
    Silently halts cell execution
    '''
    def _render_traceback_(self):
        pass
    
    
def print_modes():
    print("Program modes")
    print("    (1) WHOART 용어 1 Extension\n\t    AE list.xlsx <-> WHOART-MedDRA bridge.xlsx <-> MedDRA source folder (llt.asc, mdhier.asc)")
    print("    (2) MedDRA LLT Extension \n\t    AE list.xlsx <-> MedDRA source folder (llt.asc, mdhier.asc)")
    print("    (3) 종료")
    

def clean_list(list_in):
    '''
    Helper function for process_ type functions in main.py
    Returns list_in with trailing and leading whitespace removed from each string element   

    list_in : list of string elements
    '''
    new_list = list()
    for s in list_in:
        new_list.append(s.strip())
    return new_list

def read_meddra_files(uploader_in, names_in, cols):
    '''
    Helper function for process_ type functions in main.py
    Takes in user uploaded data in uploader, renames headers according to names_in, and returns
    a dataframe with columns specified by cols
    
    uploader : FileUpload instance from ipywidget class (contains necessary file)
    names_in : list of headers to rename the existing headers (order sensitive)
    cols : subset of names_in to determine the column of return dataframe
    ''' 
    uploader = uploader_in.value[0]
    df = pd.read_csv(io.BytesIO(uploader["content"]), 
                     sep="$",
                     names=names_in)
    
    return df[cols]

def manual_identification(columns, missing, filename="WHOART-MEDRA bridge"):
    '''
    Helper function for _identify type functions in utility.py
    Prompts user to identify missing string heade in a list of possible headers in columns. 
    If missing is in columns, return corresponding match in columns. Otherwise, return empty string
    - missing : string header 
    - columns : list of strings to prompt user for match with missing
    - filename : string filename used as reference information for the user
    '''
    
    print("*" * 40)
    print("{} 파일에서 '{}'을 찾지 못했습니다.".format(filename, missing))
    print("{} 파일 제목:".format(filename))
    for i, col in enumerate(columns):
        print("    ({}) {}".format(i, col))
        
    response = input("위에 제목 중 '{}' 컬럼이 있음 (y) 없음 (n) 종료 (q): ".format(missing))
    while response != "y" and response != "n" and response != "q":
        print("잘못 입력. 다시 선택하세요.")
        response = input("위에 제목 중 '{}' 컬럼이 있음 (y) 없음 (n) 종료 (q): ".format(missing))
            
    if response == "y":
        choice_idx = input("    '{}' 컬럼을 숫자로 선택하세요: ".format(missing))

        while not choice_idx.isdigit():
            choice_idx = input("    '{}' 컬럼을 숫자로 다시 선택하세요 (예: 2): ".format(missing))

        return columns[int(choice_idx)]
    
    if response == "q":
        raise StopExecution
        
    return ""


def confirmation(actual, test):
    '''
    Helper function for _identify type functions in utility.py
    Prompts user whether test is equivalent to actual. Returns test if true. Otherwise, return empty string.
    - actual : string 
    - test : string
    '''
    response = input("'{}'이 {} 인지 확인 (y/n): ".format(test, actual))
    while response != "y" and response != "n":
        response = input("'{}'이 {} 인지 다시 확인 (y/n): ".format(test, actual))
        
    if response == "y":
        return test
    return ""

def bridge_identify(columns):
    '''
    Helper function for process_bridge() in utility.py
    Given the list of columns in WHOART-MEDDRA bridge file, prompts user and identifies the WHOART column and LLT Code column. 
    Returns the exact header for the WHOART column and LLT Code column grouped as a list (invariant order) i.e., [<WHOART column>, <LLT Code column>]
    
    - columns : list of columns in WHOART-MEDDRA bridge file
    '''
    print("=" * 40)
    print("WHOART-MEDRA bridge file")
    print("=" * 40)
    
    whoart = ""
    llt = ""
    for col in columns:
        if not whoart:
            # WHOART column not identified yet
            if "용어" in col and "1" in col:
                whoart = confirmation(actual="WHOART 용어1", test=col)
        
        if not llt:
            if "llt" in col.lower() or "code" in col.lower():
                llt = confirmation(actual="MedDRA LLT Code", test=col)
               
    
    while not llt:
        print("'LLT code'랑 'WHOART 용어1' 다 필요합니다.")
        llt = manual_identification(columns, "LLT code")
    while not whoart:
        print("'LLT code'랑 'WHOART 용어1' 다 필요합니다.")
        whoart = manual_identification(columns, "WHOART 용어1")
        
    
    return [whoart, llt]

def ae_identify(columns, mode):
    '''
    Helper function for process_ae function in main.py
    Given the list of columns in AE list file, 
    prompts user and identifies the exact column headers for 
    1. Case Number (if present, empty string otherwise), 
    2. WHOART column, and 
    3. LLT Term column 
    grouped together as a list (invariant order) i.e., returns [<Case Number (optional)>, <WHOART column> EOR <LLT Term column>].
    
    - columns : list of columns in AE list file
    - mode={"1", "2"} : AE list is used for both modes and contains different headers accoding to each mode
        See description in readme for more details
    
    * 2.2 : 'key' is a new keyword for case number column
    '''
    print("=" * 40)
    print("AE list file")
    print("=" * 40)
    
    if mode == "1":
        critical_column = "WHOART 용어1"
    else:
        critical_column = "LLT Term"
    
    case_id = ""
    term = ""
    for col in columns:
        if not case_id:
            # if not identified yet
            lower = col.lower()
            if "kd" in lower or "case" in lower or "key" in lower or "number" in lower or "#" in lower:
                case_id = confirmation(actual="Case number", test=col)
                
        if not term:
            # if not identified yet
            lower = col.lower()
            
            if mode == "1":
                # Search for WHOART if mode 1
                if "who" in lower or "art" in lower or "용어" in lower or "1" in lower:
                    term = confirmation(actual=critical_column, test=col)
            else:
                # Search for LLT term if mode 2
                if "llt" in lower or "term" in lower or ("lower" in lower and "level" in lower and "term" in lower):
                    term = confirmation(actual=critical_column + " (언어 주의)", test=col)
          
    # Case Number is optional
    if not case_id:
        case_id = manual_identification(columns, "Case number", "AE list")

    # Ensure that either WHOART term or LLT term is present 
    while not term:
        term = manual_identification(columns, critical_column, "AE list")
    
        
    return [case_id, term]


def prompt_search_parameters():
    '''
    Helper function for connect function in main.py file
    Prompts user for two parameters used for find similar string functionality in connect function
    1. Threshold (0, 1)
    2. Maximum number of similar strings to be returned (N)
    Returns as a tuple (eps, N)
    '''
    eps = input("- 유사성 임계값 (0=모두 매치, 1=매치 없음) (추천 0.6): ")
    while not eps.isdigit or float(eps) < 0 or float(eps) > 1:
        print("0과 1 사이만 가능")
        eps = input("- 유사성 임계값 (0=모두 매치, 1=매치 없음) (추천 0.6): ")

    N = input("- 유사 단어의 최대 수 (추천 5): ")
    while not N.isdigit:
        N = input("- 유사 단어의 최대 수 (추천 5): ")
        
    return eps, N