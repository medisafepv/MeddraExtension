**GENERATE MEDDRA TERMS**

Program modes:

1. **WHOART 용어 1 Extension**

`AE list.xlsx`에 있는 WHOART 용어1을 `WHOART-MedDRA Bridge.xlsx`에 매칭한 후, `llt.asc`/`mdhier.asc` 에 있는 MedDRA SOC 및 PT 컬럼을 붙여 놓기.

![Mode 1](images/mode1.jpeg)

Required files: 
* `AE list.xlsx`
* `WHOART-MedDRA Bridge.xlsx`
* MedDRA 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `llt.asc`, `mdhier.asc`

 
2. **MedDRA LLT Extension** 

`AE list.xlsx`에 있는 MedDRA LLT을 `llt.asc`/`mdhier.asc` 에 있는 MedDRA SOC 및 PT 컬럼을 붙여 놓기.

![Mode 3](images/mode2.jpeg)

Required files:
* `AE list.xlsx`
    * _LLT Term (english, 한국어, etc.)_
* MedDRA 폴더 $\rightarrow$ MedAscii 폴더 $\rightarrow$ `llt.asc`, `mdhier.asc`


**INSTRUCTIONS**
1. [https://mybinder.org/v2/gh/medisafepv/MeddraExtension/main](https://mybinder.org/v2/gh/medisafepv/MeddraExtension/main)

2. 왼쪽 파일 탐색기 패널에서 `final_WM.ipynb` 더블클릭
