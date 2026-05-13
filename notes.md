Future work should be an option to remove ALB and TSB considerations in favor of TSS ramp rate. For example look at the following output. Notice how the daily TSS rises quickly then falls back down again before settling into a slow rise. I've thought about different ways to smooth this out; in fact, the ALB feature was created in order to smooth this out. I realized that there is a very easy way to fix it though: the same thing is reflected in the weekly calculation, with the TSS ramp rate above 4.0 before settling back to 4.0. With this in mind, I think we can almost completely abandon the CTL/ATL balance ratio (TSB), just focusing on daily/weekly changes in CTL. (e.g. have TSS ramp rate as the input rather than TSB, in this case 4.0 TSS/week)

--- Offline Training Load Projection Calculator ---

--- Model Time Periods ---
Enter CTL period in days (e.g., 40): 42
Enter ATL period in days (e.g., 4): 7

--- Model Inputs ---
Enter Initial CTL: 92
Enter Initial ATL: 62
Enter Target CTL (CTL final): 160
Enter Final Target TSB (CTL - ATL) to aim for daily: -20
Enter Minimum ALB (ATL_morning - Daily_TSS) you can take (e.g., -30; default -200.0): -40

Calculating days to reach CTL 160.0 ...

It will take approximately 115 days to reach a CTL of 160.02.
Final CTL: 160.02, Final ATL: 180.02
Final Actual TSB (CTL-ATL): -20.00
Final Actual ALB (ATL_morning - TSS): -4.00
Final Shape (2\*CTL - ATL): 140.02
Average TSS needed per day: 151.52
Peak TSS during entire period: 183.45

---

Show full daily progression in console? (yes/no): yes

Daily Progression (Day: EffTSB_Trg, ActualTSS, CTL, ATL, ActualTSB, ActualALB, Shape):
Start: ---, ---, CTL=92.00, ATL=62.00, TSB=30.00, ALB=N/A, Shape=122.00
Day 1: EffTSBTrg=24.52, TSS=102.00, CTL=92.24, ATL=67.71, TSBAct=24.52, ALBAct=-40.00, Shape=116.76
Day 2: EffTSBTrg=19.18, TSS=107.71, CTL=92.61, ATL=73.43, TSBAct=19.18, ALBAct=-40.00, Shape=111.78
Day 3: EffTSBTrg=13.96, TSS=113.43, CTL=93.10, ATL=79.14, TSBAct=13.96, ALBAct=-40.00, Shape=107.06
Day 4: EffTSBTrg=8.87, TSS=119.14, CTL=93.72, ATL=84.86, TSBAct=8.87, ALBAct=-40.00, Shape=102.59
Day 5: EffTSBTrg=3.89, TSS=124.86, CTL=94.46, ATL=90.57, TSBAct=3.89, ALBAct=-40.00, Shape=98.36
Day 6: EffTSBTrg=-0.96, TSS=130.57, CTL=95.32, ATL=96.29, TSBAct=-0.96, ALBAct=-40.00, Shape=94.36
Day 7: EffTSBTrg=-5.70, TSS=136.29, CTL=96.30, ATL=102.00, TSBAct=-5.70, ALBAct=-40.00, Shape=90.60
Day 8: EffTSBTrg=-10.33, TSS=142.00, CTL=97.39, ATL=107.71, TSBAct=-10.33, ALBAct=-40.00, Shape=87.06
Day 9: EffTSBTrg=-14.84, TSS=147.71, CTL=98.59, ATL=113.43, TSBAct=-14.84, ALBAct=-40.00, Shape=83.74
Day 10: EffTSBTrg=-19.25, TSS=153.43, CTL=99.89, ATL=119.14, TSBAct=-19.25, ALBAct=-40.00, Shape=80.64
Day 11: EffTSBTrg=-20.00, TSS=129.28, CTL=100.59, ATL=120.59, TSBAct=-20.00, ALBAct=-10.13, Shape=80.59
Day 12: EffTSBTrg=-20.00, TSS=124.59, CTL=101.16, ATL=121.16, TSBAct=-20.00, ALBAct=-4.00, Shape=81.16
Day 13: EffTSBTrg=-20.00, TSS=125.16, CTL=101.73, ATL=121.73, TSBAct=-20.00, ALBAct=-4.00, Shape=81.73
Day 14: EffTSBTrg=-20.00, TSS=125.73, CTL=102.30, ATL=122.30, TSBAct=-20.00, ALBAct=-4.00, Shape=82.30
Day 15: EffTSBTrg=-20.00, TSS=126.30, CTL=102.88, ATL=122.88, TSBAct=-20.00, ALBAct=-4.00, Shape=82.88
Day 16: EffTSBTrg=-20.00, TSS=126.88, CTL=103.45, ATL=123.45, TSBAct=-20.00, ALBAct=-4.00, Shape=83.45
Day 17: EffTSBTrg=-20.00, TSS=127.45, CTL=104.02, ATL=124.02, TSBAct=-20.00, ALBAct=-4.00, Shape=84.02
Day 18: EffTSBTrg=-20.00, TSS=128.02, CTL=104.59, ATL=124.59, TSBAct=-20.00, ALBAct=-4.00, Shape=84.59
Day 19: EffTSBTrg=-20.00, TSS=128.59, CTL=105.16, ATL=125.16, TSBAct=-20.00, ALBAct=-4.00, Shape=85.16
Day 20: EffTSBTrg=-20.00, TSS=129.16, CTL=105.73, ATL=125.73, TSBAct=-20.00, ALBAct=-4.00, Shape=85.73
Day 21: EffTSBTrg=-20.00, TSS=129.73, CTL=106.30, ATL=126.30, TSBAct=-20.00, ALBAct=-4.00, Shape=86.30
Day 22: EffTSBTrg=-20.00, TSS=130.30, CTL=106.88, ATL=126.88, TSBAct=-20.00, ALBAct=-4.00, Shape=86.88
Day 23: EffTSBTrg=-20.00, TSS=130.88, CTL=107.45, ATL=127.45, TSBAct=-20.00, ALBAct=-4.00, Shape=87.45
Day 24: EffTSBTrg=-20.00, TSS=131.45, CTL=108.02, ATL=128.02, TSBAct=-20.00, ALBAct=-4.00, Shape=88.02
Day 25: EffTSBTrg=-20.00, TSS=132.02, CTL=108.59, ATL=128.59, TSBAct=-20.00, ALBAct=-4.00, Shape=88.59
Day 26: EffTSBTrg=-20.00, TSS=132.59, CTL=109.16, ATL=129.16, TSBAct=-20.00, ALBAct=-4.00, Shape=89.16
Day 27: EffTSBTrg=-20.00, TSS=133.16, CTL=109.73, ATL=129.73, TSBAct=-20.00, ALBAct=-4.00, Shape=89.73
Day 28: EffTSBTrg=-20.00, TSS=133.73, CTL=110.30, ATL=130.30, TSBAct=-20.00, ALBAct=-4.00, Shape=90.30
Day 29: EffTSBTrg=-20.00, TSS=134.30, CTL=110.88, ATL=130.88, TSBAct=-20.00, ALBAct=-4.00, Shape=90.88
Day 30: EffTSBTrg=-20.00, TSS=134.88, CTL=111.45, ATL=131.45, TSBAct=-20.00, ALBAct=-4.00, Shape=91.45
Day 31: EffTSBTrg=-20.00, TSS=135.45, CTL=112.02, ATL=132.02, TSBAct=-20.00, ALBAct=-4.00, Shape=92.02
Day 32: EffTSBTrg=-20.00, TSS=136.02, CTL=112.59, ATL=132.59, TSBAct=-20.00, ALBAct=-4.00, Shape=92.59
Day 33: EffTSBTrg=-20.00, TSS=136.59, CTL=113.16, ATL=133.16, TSBAct=-20.00, ALBAct=-4.00, Shape=93.16
Day 34: EffTSBTrg=-20.00, TSS=137.16, CTL=113.73, ATL=133.73, TSBAct=-20.00, ALBAct=-4.00, Shape=93.73
Day 35: EffTSBTrg=-20.00, TSS=137.73, CTL=114.30, ATL=134.30, TSBAct=-20.00, ALBAct=-4.00, Shape=94.30
Day 36: EffTSBTrg=-20.00, TSS=138.30, CTL=114.88, ATL=134.88, TSBAct=-20.00, ALBAct=-4.00, Shape=94.88
Day 37: EffTSBTrg=-20.00, TSS=138.88, CTL=115.45, ATL=135.45, TSBAct=-20.00, ALBAct=-4.00, Shape=95.45
Day 38: EffTSBTrg=-20.00, TSS=139.45, CTL=116.02, ATL=136.02, TSBAct=-20.00, ALBAct=-4.00, Shape=96.02
Day 39: EffTSBTrg=-20.00, TSS=140.02, CTL=116.59, ATL=136.59, TSBAct=-20.00, ALBAct=-4.00, Shape=96.59
Day 40: EffTSBTrg=-20.00, TSS=140.59, CTL=117.16, ATL=137.16, TSBAct=-20.00, ALBAct=-4.00, Shape=97.16
Day 41: EffTSBTrg=-20.00, TSS=141.16, CTL=117.73, ATL=137.73, TSBAct=-20.00, ALBAct=-4.00, Shape=97.73
Day 42: EffTSBTrg=-20.00, TSS=141.73, CTL=118.30, ATL=138.30, TSBAct=-20.00, ALBAct=-4.00, Shape=98.30
Day 43: EffTSBTrg=-20.00, TSS=142.30, CTL=118.88, ATL=138.88, TSBAct=-20.00, ALBAct=-4.00, Shape=98.88
Day 44: EffTSBTrg=-20.00, TSS=142.88, CTL=119.45, ATL=139.45, TSBAct=-20.00, ALBAct=-4.00, Shape=99.45
Day 45: EffTSBTrg=-20.00, TSS=143.45, CTL=120.02, ATL=140.02, TSBAct=-20.00, ALBAct=-4.00, Shape=100.02
Day 46: EffTSBTrg=-20.00, TSS=144.02, CTL=120.59, ATL=140.59, TSBAct=-20.00, ALBAct=-4.00, Shape=100.59
Day 47: EffTSBTrg=-20.00, TSS=144.59, CTL=121.16, ATL=141.16, TSBAct=-20.00, ALBAct=-4.00, Shape=101.16
Day 48: EffTSBTrg=-20.00, TSS=145.16, CTL=121.73, ATL=141.73, TSBAct=-20.00, ALBAct=-4.00, Shape=101.73
Day 49: EffTSBTrg=-20.00, TSS=145.73, CTL=122.30, ATL=142.30, TSBAct=-20.00, ALBAct=-4.00, Shape=102.30
Day 50: EffTSBTrg=-20.00, TSS=146.30, CTL=122.88, ATL=142.88, TSBAct=-20.00, ALBAct=-4.00, Shape=102.88
Day 51: EffTSBTrg=-20.00, TSS=146.88, CTL=123.45, ATL=143.45, TSBAct=-20.00, ALBAct=-4.00, Shape=103.45
Day 52: EffTSBTrg=-20.00, TSS=147.45, CTL=124.02, ATL=144.02, TSBAct=-20.00, ALBAct=-4.00, Shape=104.02
Day 53: EffTSBTrg=-20.00, TSS=148.02, CTL=124.59, ATL=144.59, TSBAct=-20.00, ALBAct=-4.00, Shape=104.59
Day 54: EffTSBTrg=-20.00, TSS=148.59, CTL=125.16, ATL=145.16, TSBAct=-20.00, ALBAct=-4.00, Shape=105.16
Day 55: EffTSBTrg=-20.00, TSS=149.16, CTL=125.73, ATL=145.73, TSBAct=-20.00, ALBAct=-4.00, Shape=105.73
Day 56: EffTSBTrg=-20.00, TSS=149.73, CTL=126.30, ATL=146.30, TSBAct=-20.00, ALBAct=-4.00, Shape=106.30
Day 57: EffTSBTrg=-20.00, TSS=150.30, CTL=126.88, ATL=146.88, TSBAct=-20.00, ALBAct=-4.00, Shape=106.88
Day 58: EffTSBTrg=-20.00, TSS=150.88, CTL=127.45, ATL=147.45, TSBAct=-20.00, ALBAct=-4.00, Shape=107.45
Day 59: EffTSBTrg=-20.00, TSS=151.45, CTL=128.02, ATL=148.02, TSBAct=-20.00, ALBAct=-4.00, Shape=108.02
Day 60: EffTSBTrg=-20.00, TSS=152.02, CTL=128.59, ATL=148.59, TSBAct=-20.00, ALBAct=-4.00, Shape=108.59
Day 61: EffTSBTrg=-20.00, TSS=152.59, CTL=129.16, ATL=149.16, TSBAct=-20.00, ALBAct=-4.00, Shape=109.16
Day 62: EffTSBTrg=-20.00, TSS=153.16, CTL=129.73, ATL=149.73, TSBAct=-20.00, ALBAct=-4.00, Shape=109.73
Day 63: EffTSBTrg=-20.00, TSS=153.73, CTL=130.30, ATL=150.30, TSBAct=-20.00, ALBAct=-4.00, Shape=110.30
Day 64: EffTSBTrg=-20.00, TSS=154.30, CTL=130.88, ATL=150.88, TSBAct=-20.00, ALBAct=-4.00, Shape=110.88
Day 65: EffTSBTrg=-20.00, TSS=154.88, CTL=131.45, ATL=151.45, TSBAct=-20.00, ALBAct=-4.00, Shape=111.45
Day 66: EffTSBTrg=-20.00, TSS=155.45, CTL=132.02, ATL=152.02, TSBAct=-20.00, ALBAct=-4.00, Shape=112.02
Day 67: EffTSBTrg=-20.00, TSS=156.02, CTL=132.59, ATL=152.59, TSBAct=-20.00, ALBAct=-4.00, Shape=112.59
Day 68: EffTSBTrg=-20.00, TSS=156.59, CTL=133.16, ATL=153.16, TSBAct=-20.00, ALBAct=-4.00, Shape=113.16
Day 69: EffTSBTrg=-20.00, TSS=157.16, CTL=133.73, ATL=153.73, TSBAct=-20.00, ALBAct=-4.00, Shape=113.73
Day 70: EffTSBTrg=-20.00, TSS=157.73, CTL=134.30, ATL=154.30, TSBAct=-20.00, ALBAct=-4.00, Shape=114.30
Day 71: EffTSBTrg=-20.00, TSS=158.30, CTL=134.88, ATL=154.88, TSBAct=-20.00, ALBAct=-4.00, Shape=114.88
Day 72: EffTSBTrg=-20.00, TSS=158.88, CTL=135.45, ATL=155.45, TSBAct=-20.00, ALBAct=-4.00, Shape=115.45
Day 73: EffTSBTrg=-20.00, TSS=159.45, CTL=136.02, ATL=156.02, TSBAct=-20.00, ALBAct=-4.00, Shape=116.02
Day 74: EffTSBTrg=-20.00, TSS=160.02, CTL=136.59, ATL=156.59, TSBAct=-20.00, ALBAct=-4.00, Shape=116.59
Day 75: EffTSBTrg=-20.00, TSS=160.59, CTL=137.16, ATL=157.16, TSBAct=-20.00, ALBAct=-4.00, Shape=117.16
Day 76: EffTSBTrg=-20.00, TSS=161.16, CTL=137.73, ATL=157.73, TSBAct=-20.00, ALBAct=-4.00, Shape=117.73
Day 77: EffTSBTrg=-20.00, TSS=161.73, CTL=138.30, ATL=158.30, TSBAct=-20.00, ALBAct=-4.00, Shape=118.30
Day 78: EffTSBTrg=-20.00, TSS=162.30, CTL=138.88, ATL=158.88, TSBAct=-20.00, ALBAct=-4.00, Shape=118.88
Day 79: EffTSBTrg=-20.00, TSS=162.88, CTL=139.45, ATL=159.45, TSBAct=-20.00, ALBAct=-4.00, Shape=119.45
Day 80: EffTSBTrg=-20.00, TSS=163.45, CTL=140.02, ATL=160.02, TSBAct=-20.00, ALBAct=-4.00, Shape=120.02
Day 81: EffTSBTrg=-20.00, TSS=164.02, CTL=140.59, ATL=160.59, TSBAct=-20.00, ALBAct=-4.00, Shape=120.59
Day 82: EffTSBTrg=-20.00, TSS=164.59, CTL=141.16, ATL=161.16, TSBAct=-20.00, ALBAct=-4.00, Shape=121.16
Day 83: EffTSBTrg=-20.00, TSS=165.16, CTL=141.73, ATL=161.73, TSBAct=-20.00, ALBAct=-4.00, Shape=121.73
Day 84: EffTSBTrg=-20.00, TSS=165.73, CTL=142.30, ATL=162.30, TSBAct=-20.00, ALBAct=-4.00, Shape=122.30
Day 85: EffTSBTrg=-20.00, TSS=166.30, CTL=142.88, ATL=162.88, TSBAct=-20.00, ALBAct=-4.00, Shape=122.88
Day 86: EffTSBTrg=-20.00, TSS=166.88, CTL=143.45, ATL=163.45, TSBAct=-20.00, ALBAct=-4.00, Shape=123.45
Day 87: EffTSBTrg=-20.00, TSS=167.45, CTL=144.02, ATL=164.02, TSBAct=-20.00, ALBAct=-4.00, Shape=124.02
Day 88: EffTSBTrg=-20.00, TSS=168.02, CTL=144.59, ATL=164.59, TSBAct=-20.00, ALBAct=-4.00, Shape=124.59
Day 89: EffTSBTrg=-20.00, TSS=168.59, CTL=145.16, ATL=165.16, TSBAct=-20.00, ALBAct=-4.00, Shape=125.16
Day 90: EffTSBTrg=-20.00, TSS=169.16, CTL=145.73, ATL=165.73, TSBAct=-20.00, ALBAct=-4.00, Shape=125.73
Day 91: EffTSBTrg=-20.00, TSS=169.73, CTL=146.30, ATL=166.30, TSBAct=-20.00, ALBAct=-4.00, Shape=126.30
Day 92: EffTSBTrg=-20.00, TSS=170.30, CTL=146.88, ATL=166.88, TSBAct=-20.00, ALBAct=-4.00, Shape=126.88
Day 93: EffTSBTrg=-20.00, TSS=170.88, CTL=147.45, ATL=167.45, TSBAct=-20.00, ALBAct=-4.00, Shape=127.45
Day 94: EffTSBTrg=-20.00, TSS=171.45, CTL=148.02, ATL=168.02, TSBAct=-20.00, ALBAct=-4.00, Shape=128.02
Day 95: EffTSBTrg=-20.00, TSS=172.02, CTL=148.59, ATL=168.59, TSBAct=-20.00, ALBAct=-4.00, Shape=128.59
Day 96: EffTSBTrg=-20.00, TSS=172.59, CTL=149.16, ATL=169.16, TSBAct=-20.00, ALBAct=-4.00, Shape=129.16
Day 97: EffTSBTrg=-20.00, TSS=173.16, CTL=149.73, ATL=169.73, TSBAct=-20.00, ALBAct=-4.00, Shape=129.73
Day 98: EffTSBTrg=-20.00, TSS=173.73, CTL=150.30, ATL=170.30, TSBAct=-20.00, ALBAct=-4.00, Shape=130.30
Day 99: EffTSBTrg=-20.00, TSS=174.30, CTL=150.88, ATL=170.88, TSBAct=-20.00, ALBAct=-4.00, Shape=130.88
Day 100: EffTSBTrg=-20.00, TSS=174.88, CTL=151.45, ATL=171.45, TSBAct=-20.00, ALBAct=-4.00, Shape=131.45
Day 101: EffTSBTrg=-20.00, TSS=175.45, CTL=152.02, ATL=172.02, TSBAct=-20.00, ALBAct=-4.00, Shape=132.02
Day 102: EffTSBTrg=-20.00, TSS=176.02, CTL=152.59, ATL=172.59, TSBAct=-20.00, ALBAct=-4.00, Shape=132.59
Day 103: EffTSBTrg=-20.00, TSS=176.59, CTL=153.16, ATL=173.16, TSBAct=-20.00, ALBAct=-4.00, Shape=133.16
Day 104: EffTSBTrg=-20.00, TSS=177.16, CTL=153.73, ATL=173.73, TSBAct=-20.00, ALBAct=-4.00, Shape=133.73
Day 105: EffTSBTrg=-20.00, TSS=177.73, CTL=154.30, ATL=174.30, TSBAct=-20.00, ALBAct=-4.00, Shape=134.30
Day 106: EffTSBTrg=-20.00, TSS=178.30, CTL=154.88, ATL=174.88, TSBAct=-20.00, ALBAct=-4.00, Shape=134.88
Day 107: EffTSBTrg=-20.00, TSS=178.88, CTL=155.45, ATL=175.45, TSBAct=-20.00, ALBAct=-4.00, Shape=135.45
Day 108: EffTSBTrg=-20.00, TSS=179.45, CTL=156.02, ATL=176.02, TSBAct=-20.00, ALBAct=-4.00, Shape=136.02
Day 109: EffTSBTrg=-20.00, TSS=180.02, CTL=156.59, ATL=176.59, TSBAct=-20.00, ALBAct=-4.00, Shape=136.59
Day 110: EffTSBTrg=-20.00, TSS=180.59, CTL=157.16, ATL=177.16, TSBAct=-20.00, ALBAct=-4.00, Shape=137.16
Day 111: EffTSBTrg=-20.00, TSS=181.16, CTL=157.73, ATL=177.73, TSBAct=-20.00, ALBAct=-4.00, Shape=137.73
Day 112: EffTSBTrg=-20.00, TSS=181.73, CTL=158.30, ATL=178.30, TSBAct=-20.00, ALBAct=-4.00, Shape=138.30
Day 113: EffTSBTrg=-20.00, TSS=182.30, CTL=158.88, ATL=178.88, TSBAct=-20.00, ALBAct=-4.00, Shape=138.88
Day 114: EffTSBTrg=-20.00, TSS=182.88, CTL=159.45, ATL=179.45, TSBAct=-20.00, ALBAct=-4.00, Shape=139.45
Day 115: EffTSBTrg=-20.00, TSS=183.45, CTL=160.02, ATL=180.02, TSBAct=-20.00, ALBAct=-4.00, Shape=140.02

--- Weekly Summary ---
Week | Days | Total TSS | End CTL | End ATL | End TSB | End Shape | Ramp Rate

---

1 | 1-7 | 834 | 96.3 | 102.0 | -5.7 | 90.6 | +4.3  
2 | 8-14 | 948 | 102.3 | 122.3 | -20.0 | 82.3 | +6.0  
3 | 15-21 | 896 | 106.3 | 126.3 | -20.0 | 86.3 | +4.0  
4 | 22-28 | 924 | 110.3 | 130.3 | -20.0 | 90.3 | +4.0  
5 | 29-35 | 952 | 114.3 | 134.3 | -20.0 | 94.3 | +4.0  
6 | 36-42 | 980 | 118.3 | 138.3 | -20.0 | 98.3 | +4.0  
7 | 43-49 | 1008 | 122.3 | 142.3 | -20.0 | 102.3 | +4.0  
8 | 50-56 | 1036 | 126.3 | 146.3 | -20.0 | 106.3 | +4.0  
9 | 57-63 | 1064 | 130.3 | 150.3 | -20.0 | 110.3 | +4.0  
10 | 64-70 | 1092 | 134.3 | 154.3 | -20.0 | 114.3 | +4.0  
11 | 71-77 | 1120 | 138.3 | 158.3 | -20.0 | 118.3 | +4.0  
12 | 78-84 | 1148 | 142.3 | 162.3 | -20.0 | 122.3 | +4.0  
13 | 85-91 | 1176 | 146.3 | 166.3 | -20.0 | 126.3 | +4.0  
14 | 92-98 | 1204 | 150.3 | 170.3 | -20.0 | 130.3 | +4.0  
15 | 99-105 | 1232 | 154.3 | 174.3 | -20.0 | 134.3 | +4.0  
16 | 106-112 | 1260 | 158.3 | 178.3 | -20.0 | 138.3 | +4.0  
17 | 113-115 | 549 | 160.0 | 180.0 | -20.0 | 140.0 | +4.0

---
