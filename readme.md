# Generate MedDRA Terms

Program modes:

1. **AE list WHOART indexing**

![Mode 1](images/mode1.jpeg)

 - Required files: 
    * `AE list.xlsx`
    * `WHOART-MedDRA Bridge.xlsx`
    * MedDRA_English 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `llt.asc`
    * MedDRA_English 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `mdhier.asc`
 - Effect: `AE list.xlsx`에 있는 WHOART 용어1을 `WHOART-MedDRA Bridge.xlsx`에 매칭한 후, `llt.asc`/`mdhier.asc` 에 있는 MedDRA SOC 및 PT 컬럼을 붙여 놓기.

2. **Bridge Extension**

![Mode 2](images/mode2.jpeg)

 - Required files:
    * `WHOART-MedDRA Bridge.xlsx`
    * MedDRA_English 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `llt.asc`
    * MedDRA_English 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `mdhier.asc`
 - Effect: `WHOART-MedDRA Bridge.xlsx`에 있는 MedDRA LLT을 `llt.asc`/`mdhier.asc` 에 있는 MedDRA SOC 및 PT 컬럼을 붙여 놓기.
 
3. **AE list Extension**

![Mode 3](images/mode3.jpeg)

 - Required files: 
    * `AE list.xlsx`
    * MedDRA_English 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `llt.asc`
    * MedDRA_English 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `mdhier.asc`
 - Effect: `AE list.xlsx`에 있는 MedDRA LLT을 `llt.asc`/`mdhier.asc` 에 있는 MedDRA SOC 및 PT 컬럼을 붙여 놓기.



### Instructions
1. Binder site 방문 (https://mybinder.org/):
 - GitHub 선택 확인 후 입력: `https://github.com/sion23/ListConverter`
 - Git ref 입력: `master`

2. Launch (1-5분)

3. 왼쪽 파일 탐색기 패널에서 `final_WM.ipynb` 더블클릭

프로그램 종료: 브라우저 창을 닫은 후, 저장에 대한 메시지가 나타나면 저장 안 함을 클릭하세요

#### 참고 노트

어느 시점에서 입력 / 선택을 잘못한 경우, 중지 누르시고 (square button), 필요하신 cell을 제실행 하세요 (1. cell 선택 2. cell 실행 `Shift` + `Enter`)