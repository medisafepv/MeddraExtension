import io
import pandas as pd
import re


class StopExecution(Exception):
    def _render_traceback_(self):
        pass
    
    
def print_modes():
    print("Program modes")
    print("    (1) AE list WHOART indexing\n\t    AE list.xlsx <-> WHOART-MedDRA bridge.xlsx <-> MedDRA source folder (llt.asc, mdhier.asc)")
    print("    (2) Bridge extension\n\t    Bridge.xlsx <-> MedDRA source folder (llt.asc, mdhier.asc)")
    print("    (3) AE list extension\n\t    AE list.xlsx <-> MedDRA source folder (llt.asc, mdhier.asc)")
    print("    (4) 종료")
    

def clean_list(list_in):
    '''
    Helper function for identifying columns in AE list file
    Removes trailing and leading whitespace from each string element in list
    Maintains order
    '''
    new_list = list()
    for old in list_in:
        new = re.sub("^(\s|[ \t]|[\n])*", "", old)
        new = re.sub("(\s|[ \t]|[\n])*$", "", new)
        new_list.append(new)
        
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
    print("*" * 40)
    print("{} 파일에서 '{}'을 찾지 못했습니다.".format(filename, missing))
    print("{} 파일 제목:".format(filename))
    for i, col in enumerate(columns):
        print("    ({}) {}".format(i, col))
        
    response = input("위에 제목 중 '{}' 컬럼이 있음 (y) 없음 (n) 종료 (q): ".format(missing))
    while response != "y" and response != "n" and response != "q":
        print("잘못 입력. 다시 선택해주세요.")
        response = input("위에 제목 중 '{}' 컬럼이 있음 (y) 없음 (n) 종료 (q): ".format(missing))
            
    if response == "y":
        choice_idx = input("    '{}' 컬럼을 숫자로 선택해주세요: ".format(missing))

        while not choice_idx.isdigit():
            choice_idx = input("    '{}' 컬럼을 숫자로 다시 선택해주세요 (예: 2): ".format(missing))

        return columns[int(choice_idx)]
    
    if response == "q":
        raise StopExecution
        
    return ""


def confirmation(actual, test):
    response = input("'{}'이 {} 인지 확인 해주세요 (y/n): ".format(test, actual))
    while response != "y" and response != "n":
        response = input("'{}'이 {} 인지 다시 확인 해주세요 (y/n): ".format(test, actual))
        
    if response == "y":
        return test
    return ""

def bridge_identify(columns, mode):
    '''
    Helper function for process_bridge()
    Returns [WHOART, LLT] from bridge file
    
    * 1.1 : Added mode parameter
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
               
    
    if not llt:
        llt = manual_identification(columns, "LLT code")
    if not whoart:
        whoart = manual_identification(columns, "WHOART 용어1")
    
    if mode == "1":
        while not whoart or not llt:
            # if mode 1, we need both llt code and whoart
            print("Mode 1은 'LLT code'랑 'WHOART 용어1' 다 필요합니다.")
            whoart = manual_identification(columns, "WHOART 용어1")
            llt = manual_identification(columns, "LLT code")
        
    while not whoart and not llt:
        print("*" * 40)
        print("WHOART-MEDRA bridge 파일에 'LLT code'나 'WHOART 용어1' 이 둘중에 하나는 필요합니다.")
        whoart = manual_identification(columns, "WHOART 용어1")
        llt = manual_identification(columns, "LLT code")
        
    while whoart and not llt:
        # Given no LLT but WHOART 
        print("*" * 40)
        print("WHOART-MEDDRA bridge 파일에 아래 경우만 가능합니다:")
        print("    (1) LLT code")
        print("    (2) LLT code, WHOART 용어1")
        llt = manual_identification(columns, "LLT code")
    
    return [whoart, llt]

def ae_identify(columns, mode):
    '''
    Helper function for identifying columns in AE list file
    Returns [case number, whoart EOR llt code] in specified order
    '''
    print("=" * 40)
    print("AE list file")
    print("=" * 40)
    
    critical_column = "WHOART 용어1"
    if mode == "3":
        critical_column = "LLT Code"
    
    case_id = ""
    term = ""
    for col in columns:
        if not case_id:
            # if not identified yet
            lower = col.lower()
            if "kd" in lower or "no" in lower or "number" in lower or "#" in lower:
                case_id = confirmation(actual="KD NO (case number)", test=col)
                
        if not term:
            # if not identified yet
            lower = col.lower()
            
            if mode == "3":
                # Search for LLT if mode 3
                if "llt" in lower or "code" in lower or ("lower" in lower and "level" in lower and "term" in lower):
                    # Takes precedence for future proofing (WHO-ART deprecation)
                    term = confirmation(actual="LLT Code", test=col)
            else:
                # Search for WHOART if mode 1
                if "who" in lower or "art" in lower or "용어" in lower or "1" in lower:
                    term = confirmation(actual="WHOART 용어1", test=col)
                         
    if not case_id:
        case_id = manual_identification(columns, "KD NO (case number)", "AE list")

    if not term:
        term = manual_identification(columns, critical_column, "AE list")
        
    # Exeption handling
    while not term:
        term = manual_identification(columns, critical_column, "AE list")
        
    return [case_id, term]