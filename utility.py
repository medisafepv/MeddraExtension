import io
import pandas as pd


class StopExecution(Exception):
    def _render_traceback_(self):
        pass
    
    
def print_modes():
    print("Program modes")
    print("    (1) WHOART 용어 1 Extension\n\t    AE list.xlsx <-> WHOART-MedDRA bridge.xlsx <-> MedDRA source folder (llt.asc, mdhier.asc)")
    print("    (2) MedDRA LLT Extension \n\t    AE list.xlsx <-> MedDRA source folder (llt.asc, mdhier.asc)")
    print("    (3) 종료")
    

def clean_list(list_in):
    '''
    Helper function for identifying columns in AE list file
    Removes trailing and leading whitespace from each string element in list
    Maintains order
    
    * 2.0 : changed from regex to strip() method. No longer need re library.
    '''
    new_list = list()
    for s in list_in:
        new_list.append(s.strip())
    return new_list

def read_meddra_files(uploader, names_in, cols):
    '''
    Helper function for process_ type functions
    Prompts user to upload file 
    ''' 
    uploader = uploader.value
    file_name = list(uploader.keys())[0]
    df = pd.read_csv(io.BytesIO(uploader[file_name]["content"]), 
                     sep="$",
                     names=names_in)
    
    return df[cols]

def manual_identification(columns, missing, filename="WHOART-MEDRA bridge"):
    '''
    Prompts user to identify missing header in columns
    - missing : string header
    - columns : list of strings to select from
    - filename : string filename
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
    response = input("'{}'이 {} 인지 확인 (y/n): ".format(test, actual))
    while response != "y" and response != "n":
        response = input("'{}'이 {} 인지 다시 확인 (y/n): ".format(test, actual))
        
    if response == "y":
        return test
    return ""

def bridge_identify(columns):
    '''
    Helper function for process_bridge()
    Returns [WHOART, LLT] from bridge file
    
    * 1.1 : Added mode parameter
    * 2.0 : Removed mode parameter since only mode 1 processes bridge now (no need to branch paths)
    * 2.1 : No user input behaviour simplification
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
    Helper function for identifying columns in AE list file
    Returns [case number, whoart EOR llt code] in specified order
    
    * 2.0 : updated mode control to only 1 vs. 2
    * 2.1 : no user input behaviour simplified
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
            if "kd" in lower or "case" in lower or "no." in lower or "number" in lower or "#" in lower:
                case_id = confirmation(actual="KD NO (case number)", test=col)
                
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
                    # Takes precedence for future proofing (WHO-ART deprecation)
                    term = confirmation(actual=critical_column, test=col)
                    
    if not case_id:
        case_id = manual_identification(columns, "KD NO (case number)", "AE list")

    while not term:
        term = manual_identification(columns, critical_column, "AE list")
    
        
    return [case_id, term]