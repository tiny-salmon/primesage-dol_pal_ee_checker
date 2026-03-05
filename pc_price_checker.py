"""
PRIMESAGE PC ANALYZER  v8
탭 1 — 내 PC 분석  (하드웨어 감지 + 시세 + 7등급)
탭 2 — 최적 조립 추천  (예산 입력 → 최고 CPU+GPU 조합 계산)

렉 감소 포인트
  · Canvas 기반 진행바 제거 → 단순 dot 애니메이션
  · 카드 재생성 최소화 (clear + rebuild 1회)
  · after() 배치 렌더링, 스레드 분리
  · 위젯 헬퍼 함수로 코드 정리
"""

import tkinter as tk
import threading, platform, subprocess, re, webbrowser
import urllib.request, urllib.parse
from datetime import datetime

# ═══════════════════════════════════════════════
#  팔레트  (PRIMESAGE 그대로)
# ═══════════════════════════════════════════════
BG   = "#0E0E0E"
BG2  = "#141414"
BG3  = "#161616"
BDR  = "#222222"
BDR2 = "#333333"
ACC  = "#CAFF00"
ACCH = "#EAFF88"
TXT  = "#EAEAEA"
TMID = "#CFCFCF"
TDIM = "#AAAAAA"
TSUB = "#888888"
RED  = "#FF5252"

G_COLORS = ["#CAFF00","#EAFF88","#FFFFFF","#AAAAAA","#666666","#333333","#1C1C1C"]

GRADES = [
    (1100,"GODLIKE", G_COLORS[0],"#000","최고급 — 어떤 작업도 거뜬"),
    (850, "HIGH-END",G_COLORS[1],"#000","하이엔드 — 4K·고사양 OK"),
    (650, "UPPER",   G_COLORS[2],"#000","중상급 — QHD 고설정 원활"),
    (450, "MID",     G_COLORS[3],"#000","보통 — FHD 고설정 무난"),
    (250, "LOWER",   G_COLORS[4],TXT,   "중하 — FHD 중간설정"),
    (100, "LOW",     G_COLORS[5],TDIM,  "하급 — 사무·유튜브"),
    (0,   "JUNK",    G_COLORS[6],TSUB,  "최하 — 구형 기기"),
]

PART_ACC = dict(cpu=ACC, gpu=ACCH, ram=TXT, storage=TDIM, misc=BDR2)

# ═══════════════════════════════════════════════
#  점수 DB
# ═══════════════════════════════════════════════
GPU_SCORE = {
    "RTX 5090":2200,"RTX 5080":1800,"RTX 5070 Ti":1500,"RTX 5070":1280,
    "RTX 5060 Ti":980,"RTX 5060":780,
    "RTX 4090":1900,"RTX 4080 SUPER":1420,"RTX 4080":1340,
    "RTX 4070 Ti SUPER":1260,"RTX 4070 Ti":1170,"RTX 4070 SUPER":1100,
    "RTX 4070":1000,"RTX 4060 Ti":820,"RTX 4060":680,
    "RTX 3090 Ti":1160,"RTX 3090":1100,"RTX 3080 Ti":1090,
    "RTX 3080 12GB":1050,"RTX 3080":1000,
    "RTX 3070 Ti":890,"RTX 3070":840,"RTX 3060 Ti":730,
    "RTX 3060":580,"RTX 3050":430,
    "RTX 2080 Ti":790,"RTX 2080 SUPER":680,"RTX 2080":640,
    "RTX 2070 SUPER":620,"RTX 2070":580,
    "RTX 2060 SUPER":530,"RTX 2060":470,
    "GTX 1660 Ti":390,"GTX 1660 SUPER":370,"GTX 1660":340,
    "GTX 1650 SUPER":290,"GTX 1650":220,
    "GTX 1080 Ti":560,"GTX 1080":480,"GTX 1070 Ti":440,"GTX 1070":410,
    "GTX 1060 6GB":300,"GTX 1060 3GB":250,"GTX 1050 Ti":175,"GTX 1050":130,
    "GTX 980 Ti":300,"GTX 980":240,"GTX 970":200,"GTX 960":150,
    "RX 9070 XT":1280,"RX 9070":1150,
    "RX 7900 XTX":1360,"RX 7900 XT":1240,"RX 7900 GRE":1080,
    "RX 7800 XT":980,"RX 7700 XT":870,"RX 7600 XT":700,"RX 7600":630,
    "RX 6950 XT":1080,"RX 6900 XT":1020,"RX 6800 XT":980,"RX 6800":890,
    "RX 6750 XT":810,"RX 6700 XT":760,"RX 6700":720,
    "RX 6650 XT":670,"RX 6600 XT":620,"RX 6600":570,"RX 6500 XT":280,
    "RX 5700 XT":640,"RX 5700":580,"RX 5600 XT":510,"RX 5500 XT":360,
    "RX 590":290,"RX 580 8GB":260,"RX 580 4GB":230,"RX 570":210,
    "Vega 64":400,"Vega 56":340,
    "Arc B580":720,"Arc B570":620,"Arc A770":570,"Arc A750":510,"Arc A580":430,
}
CPU_SCORE = {
    "i9-14900K":2950,"i9-14900KF":2920,"i9-14900":2800,
    "i7-14700K":2500,"i7-14700KF":2480,"i7-14700":2350,
    "i5-14600K":1850,"i5-14600KF":1830,"i5-14500":1620,
    "i5-14400":1480,"i5-14400F":1460,"i3-14100":900,"i3-14100F":880,
    "i9-13900K":2900,"i9-13900KF":2870,"i9-13900":2720,
    "i7-13700K":2450,"i7-13700KF":2420,"i7-13700":2280,
    "i5-13600K":1820,"i5-13600KF":1800,"i5-13500":1580,
    "i5-13400":1450,"i5-13400F":1430,"i3-13100":880,"i3-13100F":860,
    "i9-12900K":2400,"i9-12900KF":2380,"i7-12700K":2050,"i7-12700":1950,
    "i5-12600K":1650,"i5-12600":1480,"i5-12400":1000,"i5-12400F":980,
    "i3-12100":820,"i3-12100F":800,
    "i9-11900K":1700,"i7-11700K":1520,"i7-11700":1380,
    "i5-11600K":1200,"i5-11400":1050,"i5-11400F":1030,
    "i9-10900K":1550,"i7-10700K":1370,"i5-10600K":1100,
    "i5-10400":920,"i5-10400F":900,"i3-10100":630,"i3-10100F":610,
    "i9-9900K":1250,"i7-9700K":1050,"i5-9600K":820,"i5-9400F":720,
    "i7-8700K":950,"i7-8700":880,"i5-8400":650,
    "Ryzen 9 9950X":3400,"Ryzen 9 9900X":2900,"Ryzen 7 9700X":2200,"Ryzen 5 9600X":1700,
    "Ryzen 9 7950X":3300,"Ryzen 9 7900X":2700,"Ryzen 9 7900":2500,
    "Ryzen 7 7800X3D":2100,"Ryzen 7 7700X":1950,"Ryzen 7 7700":1820,
    "Ryzen 5 7600X":1520,"Ryzen 5 7600":1430,
    "Ryzen 9 5950X":2600,"Ryzen 9 5900X":2200,"Ryzen 7 5800X3D":1600,
    "Ryzen 7 5800X":1520,"Ryzen 7 5700X":1380,"Ryzen 7 5700G":1280,
    "Ryzen 5 5600X":1220,"Ryzen 5 5600":1100,"Ryzen 5 5500":950,
    "Ryzen 9 3900X":1680,"Ryzen 9 3900":1550,"Ryzen 7 3800X":1320,"Ryzen 7 3700X":1300,
    "Ryzen 5 3600X":1050,"Ryzen 5 3600":980,"Ryzen 5 3500":780,
    "Ryzen 7 2700X":900,"Ryzen 7 2700":820,"Ryzen 5 2600X":750,"Ryzen 5 2600":700,
}

# ═══════════════════════════════════════════════
#  가격 DB
# ═══════════════════════════════════════════════
PRICE_CPU = {
    "Core i9-14900K":(450000,650000),"Core i9-14900KF":(420000,620000),
    "Core i7-14700K":(380000,520000),"Core i7-14700KF":(360000,500000),
    "Core i5-14600K":(280000,400000),"Core i5-14600KF":(260000,380000),
    "Core i9-13900K":(400000,600000),"Core i9-13900KF":(380000,560000),
    "Core i7-13700K":(320000,460000),"Core i7-13700KF":(300000,440000),
    "Core i5-13600K":(230000,350000),"Core i5-13600KF":(210000,330000),
    "Core i5-13500":(190000,290000),"Core i5-13400":(170000,270000),
    "Core i5-13400F":(155000,250000),"Core i3-13100":(110000,180000),
    "Core i3-13100F":(95000,160000),
    "Core i9-12900K":(300000,450000),"Core i7-12700K":(250000,380000),
    "Core i5-12600K":(180000,280000),"Core i5-12400":(130000,210000),
    "Core i5-12400F":(115000,190000),"Core i3-12100":(90000,150000),
    "Core i3-12100F":(75000,130000),
    "Core i9-11900K":(200000,320000),"Core i7-11700K":(170000,270000),
    "Core i5-11600K":(130000,210000),"Core i5-11400":(100000,170000),
    "Core i5-11400F":(90000,155000),
    "Core i9-10900K":(150000,260000),"Core i7-10700K":(130000,220000),
    "Core i5-10600K":(100000,175000),"Core i5-10400":(80000,145000),
    "Core i5-10400F":(70000,130000),
    "Ryzen 9 7950X":(550000,750000),"Ryzen 9 7900X":(400000,580000),
    "Ryzen 9 7900":(360000,520000),"Ryzen 7 7800X3D":(450000,620000),
    "Ryzen 7 7700X":(300000,440000),"Ryzen 7 7700":(270000,400000),
    "Ryzen 5 7600X":(230000,340000),"Ryzen 5 7600":(210000,320000),
    "Ryzen 9 5950X":(350000,520000),"Ryzen 9 5900X":(280000,430000),
    "Ryzen 7 5800X3D":(330000,490000),"Ryzen 7 5800X":(200000,330000),
    "Ryzen 7 5700X":(170000,280000),"Ryzen 5 5600X":(150000,250000),
    "Ryzen 5 5600":(130000,220000),"Ryzen 5 5500":(90000,160000),
    "Ryzen 9 3900X":(180000,300000),"Ryzen 7 3700X":(130000,220000),
    "Ryzen 5 3600X":(100000,175000),"Ryzen 5 3600":(85000,155000),
    "Ryzen 5 3500":(65000,120000),
}
PRICE_GPU = {
    "RTX 4090":(1700000,2200000),"RTX 4080 SUPER":(1100000,1400000),
    "RTX 4080":(1000000,1350000),"RTX 4070 Ti SUPER":(850000,1100000),
    "RTX 4070 Ti":(780000,1020000),"RTX 4070 SUPER":(680000,900000),
    "RTX 4070":(580000,780000),"RTX 4060 Ti":(420000,580000),
    "RTX 4060":(320000,450000),
    "RTX 3090 Ti":(800000,1100000),"RTX 3090":(650000,950000),
    "RTX 3080 Ti":(580000,850000),"RTX 3080 12GB":(480000,700000),
    "RTX 3080":(400000,620000),"RTX 3070 Ti":(340000,520000),
    "RTX 3070":(280000,450000),"RTX 3060 Ti":(230000,380000),
    "RTX 3060":(180000,300000),"RTX 3050":(130000,220000),
    "RTX 2080 Ti":(280000,450000),"RTX 2080 SUPER":(200000,340000),
    "RTX 2080":(180000,300000),"RTX 2070 SUPER":(160000,270000),
    "RTX 2070":(140000,240000),"RTX 2060 SUPER":(130000,220000),
    "RTX 2060":(110000,190000),
    "GTX 1660 Ti":(100000,175000),"GTX 1660 SUPER":(90000,160000),
    "GTX 1660":(80000,145000),"GTX 1650 SUPER":(70000,130000),
    "GTX 1650":(60000,115000),
    "GTX 1080 Ti":(130000,220000),"GTX 1080":(100000,170000),
    "GTX 1070 Ti":(85000,150000),"GTX 1070":(75000,135000),
    "GTX 1060 6GB":(55000,100000),"GTX 1060 3GB":(40000,80000),
    "GTX 1050 Ti":(35000,70000),
    "RX 7900 XTX":(900000,1250000),"RX 7900 XT":(750000,1050000),
    "RX 7800 XT":(480000,680000),"RX 7700 XT":(380000,550000),
    "RX 7600":(270000,390000),
    "RX 6950 XT":(500000,720000),"RX 6900 XT":(420000,620000),
    "RX 6800 XT":(350000,520000),"RX 6800":(300000,460000),
    "RX 6750 XT":(260000,400000),"RX 6700 XT":(220000,350000),
    "RX 6700":(190000,310000),"RX 6650 XT":(180000,290000),
    "RX 6600 XT":(160000,260000),"RX 6600":(140000,230000),
    "RX 6500 XT":(80000,140000),
    "RX 5700 XT":(150000,250000),"RX 5700":(130000,220000),
    "RX 5600 XT":(100000,180000),"RX 5500 XT":(80000,145000),
    "Arc A770":(200000,310000),"Arc A750":(170000,270000),
    "Arc A580":(150000,240000),
}

RELEASE_YEAR = {
    "i9-14900K":2023,"i9-14900KF":2023,"i7-14700K":2023,"i5-14600K":2023,
    "i9-13900K":2022,"i9-13900KF":2022,"i7-13700K":2022,"i5-13600K":2022,
    "i5-13400":2023,"i3-13100":2023,"i9-12900K":2021,"i7-12700K":2021,
    "i5-12600K":2021,"i5-12400":2022,"i5-12400F":2022,"i3-12100":2022,
    "i9-11900K":2021,"i7-11700K":2021,"i5-11400":2021,
    "i9-10900K":2020,"i7-10700K":2020,"i5-10400":2020,
    "i9-9900K":2018,"i7-9700K":2018,"i7-8700K":2017,
    "Ryzen 9 9950X":2024,"Ryzen 7 9700X":2024,"Ryzen 5 9600X":2024,
    "Ryzen 9 7950X":2022,"Ryzen 7 7800X3D":2023,"Ryzen 7 7700X":2022,
    "Ryzen 5 7600X":2022,"Ryzen 5 7600":2023,
    "Ryzen 9 5950X":2020,"Ryzen 7 5800X3D":2022,"Ryzen 7 5800X":2020,
    "Ryzen 5 5600X":2020,"Ryzen 5 5600":2021,"Ryzen 5 5500":2022,
    "Ryzen 9 3900X":2019,"Ryzen 7 3700X":2019,"Ryzen 5 3600":2019,
    "RTX 5090":2025,"RTX 5080":2025,"RTX 5070":2025,
    "RTX 4090":2022,"RTX 4080 SUPER":2024,"RTX 4080":2022,
    "RTX 4070 Ti SUPER":2024,"RTX 4070 Ti":2023,"RTX 4070 SUPER":2024,
    "RTX 4070":2023,"RTX 4060 Ti":2023,"RTX 4060":2023,
    "RTX 3090 Ti":2022,"RTX 3090":2020,"RTX 3080 Ti":2021,
    "RTX 3080":2020,"RTX 3070 Ti":2021,"RTX 3070":2020,
    "RTX 3060 Ti":2020,"RTX 3060":2021,"RTX 3050":2022,
    "RTX 2080 Ti":2018,"RTX 2080":2018,"RTX 2070":2018,"RTX 2060":2019,
    "GTX 1080 Ti":2017,"GTX 1080":2016,"GTX 1070":2016,"GTX 1060 6GB":2016,
    "GTX 1660 Ti":2019,"GTX 1660":2019,"GTX 1650":2019,
    "RX 9070 XT":2025,"RX 9070":2025,"RX 7900 XTX":2022,"RX 7800 XT":2023,
    "RX 7700 XT":2023,"RX 7600":2023,"RX 6900 XT":2020,"RX 6800 XT":2020,
    "RX 6800":2020,"RX 6700 XT":2021,"RX 6600 XT":2021,"RX 6600":2021,
    "RX 5700 XT":2019,"RX 5700":2019,"RX 5600 XT":2020,"Arc B580":2024,
    "Arc A770":2022,
}

# ═══════════════════════════════════════════════
#  유틸 함수
# ═══════════════════════════════════════════════
def get_grade(score):
    if not score: return None
    for ms,name,bg,fg,desc in GRADES:
        if score >= ms:
            return {"name":name,"bg":bg,"fg":fg,"desc":desc,"score":score}
    return None

def match_score(name, db):
    if not name or name == "알 수 없음": return None, None
    for k in sorted(db, key=len, reverse=True):
        if k.lower() in name.lower(): return db[k], k
    return None, None

def get_year(name):
    for k,y in RELEASE_YEAR.items():
        if k.lower() in name.lower(): return y
    return None

def calc_ram_score(gb, rtype, speed):
    base = {"DDR5":700,"DDR4":400,"DDR3":150}.get(rtype, 400)
    if rtype=="DDR5":   sb = max(-100,min(200,(speed-4800)//50)) if speed else 0
    elif rtype=="DDR4": sb = max(-100,min(150,(speed-3200)//40)) if speed else 0
    else: sb = 0
    cap = next((sc for mg,sc in [(128,350),(64,280),(32,200),(16,150),(8,80),(4,30)] if gb>=mg), 10)
    return min(1400, base+sb+cap)

def calc_storage_score(details):
    best = 0
    for d in details:
        gb=d["gb"]; ssd="SSD" in d["type"].upper()
        cap = next((sc for mg,sc in [(4000,400),(2000,300),(1000,200),(500,120),(250,60)] if gb>=mg), 20)
        best = max(best, (600 if ssd else 200)+cap)
    return min(1200, best)

# 정렬된 카탈로그 (성능 높은 순)
def _make_catalog(price_db, score_db):
    cat = []
    for name,(mn,_) in price_db.items():
        sc,_ = match_score(name, score_db)
        cat.append((name, sc or 0, mn))
    return sorted(cat, key=lambda x: x[1], reverse=True)

CPU_CAT = _make_catalog(PRICE_CPU, CPU_SCORE)
GPU_CAT = _make_catalog(PRICE_GPU, GPU_SCORE)

def recommend_build(budget):
    """예산 내 CPU+GPU 성능 합산 최대 조합 탐색 — 최소 30,000원부터"""
    # 예산 구간별 기타 비용 자동 조정
    if budget >= 500_000:
        FIXED = 200_000   # RAM 16GB + SSD 1TB + 케이스/파워
        ram_p, ssd_p, etc_p = 72_000, 80_000, 48_000
        ram_l, ssd_l = "16GB DDR4-3200", "1TB NVMe SSD"
    elif budget >= 200_000:
        FIXED = 80_000    # RAM 8GB + SSD 없음 + 최소 파워
        ram_p, ssd_p, etc_p = 40_000, 0, 40_000
        ram_l, ssd_l = "8GB DDR4", "없음 (HDD 재활용)"
    elif budget >= 80_000:
        FIXED = 30_000    # RAM만 기본 구성
        ram_p, ssd_p, etc_p = 20_000, 0, 10_000
        ram_l, ssd_l = "4GB DDR3 (최소)", "없음"
    else:
        FIXED = 0
        ram_p, ssd_p, etc_p = 0, 0, 0
        ram_l, ssd_l = "재활용", "재활용"

    if budget < FIXED + 30_000:
        return None

    parts = budget - FIXED
    best = None; best_score = -1

    for gn,gs,gp in GPU_CAT:
        if gp > parts * 0.75: continue
        rem = parts - gp
        if rem < 10_000: continue
        for cn,cs,cp in CPU_CAT:
            if cp <= rem:
                score = gs + cs
                if score > best_score:
                    best_score = score
                    best = {
                        "cpu":cn,"cpu_s":cs,"cpu_p":cp,
                        "gpu":gn,"gpu_s":gs,"gpu_p":gp,
                        "ram":ram_l,"ram_p":ram_p,
                        "ssd":ssd_l,"ssd_p":ssd_p,
                        "etc":"케이스 / 파워 / 쿨러","etc_p":etc_p,
                        "score":score,
                        "used":gp+cp+FIXED,
                        "left":budget-(gp+cp+FIXED),
                        "cpu_grade":get_grade(cs),
                        "gpu_grade":get_grade(gs),
                    }
                break
    return best

def web_price(query):
    try:
        enc = urllib.parse.quote(query)
        req = urllib.request.Request(
            f"https://search.danawa.com/dsearch.php?query={enc}&tab=main",
            headers={"User-Agent":"Mozilla/5.0","Accept-Language":"ko-KR,ko;q=0.9"})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
        nums = sorted(int(p.replace(",","")) for p in re.findall(r'([1-9][0-9,]{4,8})원',html)
                      if 10_000 <= int(p.replace(",","")) <= 5_000_000)
        if len(nums)>=2: return nums[len(nums)//4], nums[len(nums)*3//4]
        if len(nums)==1: v=nums[0]; return int(v*.85), int(v*1.15)
    except: pass
    return None

# ═══════════════════════════════════════════════
#  하드웨어 감지
# ═══════════════════════════════════════════════
def detect_hw():
    info={}; sys=platform.system()
    # CPU
    try:
        if sys=="Windows":
            import winreg
            k=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            info["cpu"]=winreg.QueryValueEx(k,"ProcessorNameString")[0].strip()
        elif sys=="Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line: info["cpu"]=line.split(":")[1].strip(); break
        elif sys=="Darwin":
            info["cpu"]=subprocess.check_output(["sysctl","-n","machdep.cpu.brand_string"]).decode().strip()
    except: info["cpu"]=platform.processor() or "알 수 없음"

    # RAM
    info.update(ram_gb=0, ram_type="DDR4", ram_speed=0)
    try:
        import psutil
        gb=round(psutil.virtual_memory().total/(1024**3))
        info["ram_gb"]=gb; info["ram"]=f"{gb}GB"
    except: info["ram"]="알 수 없음"
    if sys=="Windows":
        try:
            out=subprocess.check_output(["wmic","memorychip","get","MemoryType,Speed,Capacity"],
                stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.strip().splitlines():
                parts=line.split()
                if len(parts)>=2 and parts[0].isdigit():
                    mt=int(parts[0]); sp=int(parts[1]) if parts[1].isdigit() else 0
                    info["ram_type"]={24:"DDR3",26:"DDR4",34:"DDR5"}.get(mt,"DDR4")
                    info["ram_speed"]=sp
                    info["ram"]=f"{info['ram_gb']}GB {info['ram_type']}"+(f"-{sp}" if sp else "")
                    break
        except: pass

    # GPU
    info["gpu"]="알 수 없음"
    if sys=="Windows":
        try:
            out=subprocess.check_output(["wmic","path","win32_VideoController","get","Name"],
                stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.strip().splitlines():
                s=line.strip()
                if s and s!="Name": info["gpu"]=s; break
        except: pass
    elif sys=="Linux":
        try:
            out=subprocess.check_output(["lspci"],stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.splitlines():
                if any(x in line for x in ("VGA","3D","Display")):
                    m=re.search(r":\s+(.+?)(?:\s+\(|$)",line)
                    if m: info["gpu"]=m.group(1).strip(); break
        except: pass

    # Storage
    info["storage"]=[]; info["storage_detail"]=[]
    if sys=="Windows":
        try:
            out=subprocess.check_output(["wmic","diskdrive","get","Caption,Size,MediaType"],
                stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.strip().splitlines():
                s=line.strip()
                if not s or "Caption" in s: continue
                parts=s.rsplit(None,2)
                if len(parts)>=2:
                    try:
                        sb=int(parts[-2]) if parts[-2].isdigit() else 0
                        med=parts[-1] if not parts[-1].isdigit() else ""
                        gb=round(sb/(1024**3))
                        if gb>0:
                            t="SSD" if "SSD" in med.upper() or "Solid" in med else "HDD"
                            info["storage"].append(f"{gb}GB {t}")
                            info["storage_detail"].append({"gb":gb,"type":t})
                    except: pass
        except: pass
    if not info["storage"]:
        try:
            import psutil; seen=set()
            for p in psutil.disk_partitions():
                try:
                    gb=round(psutil.disk_usage(p.mountpoint).total/(1024**3))
                    if gb not in seen and gb>1:
                        seen.add(gb); info["storage"].append(f"{gb}GB")
                        info["storage_detail"].append({"gb":gb,"type":"SSD/HDD"})
                except: pass
        except: pass

    # Motherboard
    info["motherboard"]="알 수 없음"
    if sys=="Windows":
        try:
            out=subprocess.check_output(["wmic","baseboard","get","Manufacturer,Product"],
                stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.strip().splitlines():
                s=line.strip()
                if s and "Manufacturer" not in s: info["motherboard"]=s; break
        except: pass
    info["os"]=f"{platform.system()} {platform.release()}"
    return info

def estimate_prices(hw):
    res={}; total_min=total_max=0

    for part, pdb, sdb in [("cpu",PRICE_CPU,CPU_SCORE),("gpu",PRICE_GPU,GPU_SCORE)]:
        raw=hw.get(part,""); mn=mx=0
        for name,(a,b) in pdb.items():
            if name.lower() in raw.lower(): mn,mx=a,b; break
        sc,_=match_score(raw,sdb); wu=False
        if mn==0 and raw and raw!="알 수 없음":
            r=web_price(raw+" 중고 가격")
            if r: mn,mx=r; wu=True
        res[part]={"name":raw,"min":mn,"max":mx,"year":get_year(raw),
                   "web_used":wu,"score":sc,"grade":get_grade(sc)}
        total_min+=mn; total_max+=mx

    rg=hw.get("ram_gb",0); rt=hw.get("ram_type","DDR4"); rs=hw.get("ram_speed",0)
    rs_score=calc_ram_score(rg,rt,rs)
    ppg={"DDR5":9000,"DDR4":4500,"DDR3":2500}.get(rt,4500)
    res["ram"]={"name":hw.get("ram","알 수 없음"),
                "detail":f"{rg}GB {rt}"+(f"-{rs}" if rs else ""),
                "min":rg*int(ppg*.75),"max":rg*int(ppg*1.25),
                "year":None,"web_used":False,"score":rs_score,"grade":get_grade(rs_score)}
    total_min+=res["ram"]["min"]; total_max+=res["ram"]["max"]

    sd=hw.get("storage_detail",[]); ss=calc_storage_score(sd); s0=s1=0
    for d in sd:
        ssd="SSD" in d["type"].upper(); gb=d["gb"]
        s0+=int(gb*(80 if ssd else 25)); s1+=int(gb*(130 if ssd else 55))
    sl=" + ".join(f"{d['gb']}GB {d['type']}" for d in sd) or "알 수 없음"
    res["storage"]={"name":sl,"min":s0,"max":s1,"year":None,"web_used":False,
                    "score":ss,"grade":get_grade(ss)}
    total_min+=s0; total_max+=s1

    res["misc"]={"name":"케이스 / 파워 / 메인보드 / 쿨러","min":150000,"max":350000,
                 "year":None,"web_used":False,"score":None,"grade":None}
    res["total"]={"min":total_min+150000,"max":total_max+350000}
    return res

# ═══════════════════════════════════════════════
#  GUI 헬퍼
# ═══════════════════════════════════════════════
def lbl(parent, text="", fg=TXT, bg=BG3, size=9, bold=False, **kw):
    f = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    return tk.Label(parent, text=text, fg=fg, bg=bg, font=f, **kw)

def sep(parent, bg=BDR, height=1):
    return tk.Frame(parent, bg=bg, height=height)

def frm(parent, bg=BG3, **kw):
    return tk.Frame(parent, bg=bg, **kw)

def acc_btn(parent, text, cmd, small=False):
    """라임 배경 버튼"""
    size = 9 if small else 10
    pad = 5 if small else 7
    wrap = frm(parent, bg=ACC, cursor="hand2")
    inner = tk.Label(wrap, text=f"  {text}  ", bg=ACC, fg="#000",
                     font=("Segoe UI", size, "bold"), pady=pad, cursor="hand2")
    inner.pack()
    for w in (wrap, inner):
        w.bind("<Button-1>", lambda e: cmd())
        w.bind("<Enter>", lambda e: [wrap.config(bg=ACCH), inner.config(bg=ACCH)])
        w.bind("<Leave>", lambda e: [wrap.config(bg=ACC),  inner.config(bg=ACC)])
    return wrap

def ghost_btn(parent, text, cmd):
    """테두리 버튼"""
    b = tk.Frame(parent, bg=BG3, highlightbackground=BDR2, highlightthickness=1, cursor="hand2")
    bl = tk.Label(b, text=f"  {text}  ", bg=BG3, fg=TMID,
                  font=("Segoe UI",8), pady=5, cursor="hand2")
    bl.pack()
    for w in (b, bl):
        w.bind("<Button-1>", lambda e: cmd())
        w.bind("<Enter>", lambda e: [b.config(highlightbackground=ACC), bl.config(fg=ACC)])
        w.bind("<Leave>", lambda e: [b.config(highlightbackground=BDR2), bl.config(fg=TMID)])
    return b

def clear(frame):
    for w in frame.winfo_children(): w.destroy()

def grade_dot_row(parent, grade, bg=BG3):
    if not grade: return
    row = frm(parent, bg=bg)
    dot = frm(row, bg=grade["bg"])
    dot.config(width=8, height=8); dot.pack(side="left", pady=3); dot.pack_propagate(False)
    fg = grade["bg"] if grade["bg"] not in (G_COLORS[5], G_COLORS[6]) else TSUB
    lbl(row, f"  {grade['name']}  |  {grade['score']}점",
        fg=fg, bg=bg, size=9, bold=True).pack(side="left")
    return row

# ═══════════════════════════════════════════════
#  메인 앱
# ═══════════════════════════════════════════════
class App:
    def __init__(self, root):
        self.root = root
        root.title("프라임세이지 돌팔이체커")
        root.geometry("1080x840")
        root.configure(bg=BG)
        root.minsize(880, 580)
        self.hw = {}; self.prices = {}
        self._anim_id = None; self._anim_i = 0
        self._build()
        root.after(300, self.scan)

    # ─────────────────────────────────────────
    def _build(self):
        self._header()
        sep(self.root, BDR).pack(fill="x")
        self._statusbar()
        sep(self.root, BDR).pack(fill="x")
        self._scroll_body()

    # ── 헤더 ──────────────────────────────────
    def _header(self):
        h = frm(self.root, bg=BG)
        h.config(height=60); h.pack(fill="x"); h.pack_propagate(False)

        il = frm(h, bg=BG); il.pack(side="left", fill="y", padx=24)
        lbl(il,"프라임세이지",fg=ACC,bg=BG,size=15,bold=True).pack(side="left",pady=16)
        lbl(il,"  돌팔이체커",fg=TSUB,bg=BG,size=10).pack(side="left",pady=16)

        ir = frm(h, bg=BG); ir.pack(side="right", fill="y", padx=24, pady=14)

        for label,site in [("다나와","danawa"),("네이버쇼핑","naver"),("구글","google")]:
            b = lbl(ir,label,fg=TSUB,bg=BG,size=9)
            b.config(cursor="hand2", padx=8); b.pack(side="left")
            b.bind("<Button-1>", lambda e,s=site: self._search(s))
            b.bind("<Enter>", lambda e,w=b: w.config(fg=ACCH))
            b.bind("<Leave>", lambda e,w=b: w.config(fg=TSUB))

        acc_btn(ir, "다시 스캔", self.scan, small=True).pack(side="left", padx=(10,0))

    # ── 상태바 ────────────────────────────────
    def _statusbar(self):
        sb = frm(self.root, bg=BG2); sb.config(height=34)
        sb.pack(fill="x"); sb.pack_propagate(False)

        inner = frm(sb, bg=BG2)
        inner.pack(fill="both", expand=True, padx=24)

        self._status = tk.StringVar(value="준비 완료")
        lbl(inner, "", fg=ACC, bg=BG2, size=9, bold=True,
            textvariable=self._status).pack(side="left", pady=9)

        self._dot = frm(inner, bg=ACC)
        self._dot.config(width=6, height=6); self._dot.pack_propagate(False)
        self._dot.pack(side="left", padx=(8,0), pady=14)

    # ── 스크롤 본문 ───────────────────────────
    def _scroll_body(self):
        wrap = frm(self.root, bg=BG)
        wrap.pack(fill="both", expand=True)

        self._cv = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(wrap, orient="vertical", command=self._cv.yview,
                          bg=BG2, troughcolor=BG2)
        self._sf = frm(self._cv, bg=BG)
        self._sf.bind("<Configure>",
            lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.create_window((0,0), window=self._sf, anchor="nw")
        self._cv.configure(yscrollcommand=sb.set)
        self._cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._cv.bind_all("<MouseWheel>",
            lambda e: self._cv.yview_scroll(-1*(e.delta//120),"units"))

        self._tabs()

    # ── 탭 시스템 ─────────────────────────────
    def _tabs(self):
        bar = frm(self._sf, bg=BG2); bar.pack(fill="x")

        self._tab_btns = {}
        self._tab_frames = {}

        for key,label in [("scan","내 PC 분석"),("recommend","최적 조립 추천"),
                          ("compare","부품 비교"),("report","내 PC 보고서")]:
            b = lbl(bar, f"  {label}  ", fg=TSUB, bg=BG2, size=10)
            b.config(cursor="hand2", pady=11)
            b.pack(side="left")
            b.bind("<Button-1>", lambda e,k=key: self._tab(k))
            self._tab_btns[key] = b

            f = frm(self._sf, bg=BG)
            self._tab_frames[key] = f

        sep(self._sf, BDR).pack(fill="x")

        # 탭 내용 구성
        self._build_scan_tab(self._tab_frames["scan"])
        self._build_rec_tab(self._tab_frames["recommend"])
        self._build_compare_tab(self._tab_frames["compare"])
        self._build_report_tab(self._tab_frames["report"])

        self._tab("scan")

    def _tab(self, key):
        self._active = key
        for k,f in self._tab_frames.items():
            if k==key: f.pack(fill="x")
            else: f.pack_forget()
        for k,b in self._tab_btns.items():
            if k==key: b.config(fg=ACC, font=("Segoe UI",10,"bold"))
            else:       b.config(fg=TSUB, font=("Segoe UI",10))

    # ─────────────────────────────────────────
    #  탭 1 — 내 PC 분석
    # ─────────────────────────────────────────
    def _build_scan_tab(self, p):
        # HW 정보 패널
        hw_p = frm(p, bg=BG2); hw_p.pack(fill="x")
        hw_i = frm(hw_p, bg=BG2); hw_i.pack(fill="x", padx=24, pady=16)
        lbl(hw_i,"감지된 하드웨어",fg=TXT,bg=BG2,size=11,bold=True).pack(anchor="w",pady=(0,10))

        self._hw_os = lbl(hw_i,"",fg=TSUB,bg=BG2,size=8)
        self._hw_os.pack(anchor="w", pady=(0,8))

        grid = frm(hw_i, bg=BG2); grid.pack(fill="x")
        self._hw_lbls = {}
        for i,col in enumerate(["CPU","GPU","RAM","STORAGE","MOTHERBOARD"]):
            f = frm(grid, bg=BG2); f.grid(row=0, column=i, padx=(0,26), sticky="w")
            lbl(f,col,fg=TSUB,bg=BG2,size=8).pack(anchor="w")
            v = lbl(f,"—",fg=TXT,bg=BG2,size=9,bold=True)
            v.config(wraplength=160, justify="left"); v.pack(anchor="w")
            self._hw_lbls[col] = v

        sep(p, BDR).pack(fill="x")

        # 등급 범례
        leg = frm(p, bg=BG); leg.pack(fill="x", padx=24, pady=(16,0))
        lbl(leg,"성능 등급 기준",fg=TXT,bg=BG,size=11,bold=True).pack(anchor="w",pady=(0,8))
        row = frm(leg, bg=BG); row.pack(fill="x")
        for _,name,bg,fg,desc in GRADES:
            cell = frm(row, bg=BG3)
            cell.config(highlightbackground=BDR, highlightthickness=1)
            cell.pack(side="left", padx=(0,6))
            d = frm(cell, bg=bg); d.config(width=8,height=8)
            d.pack(side="left", padx=(10,5), pady=9); d.pack_propagate(False)
            lbl(cell,name,fg=bg if bg not in (G_COLORS[5],G_COLORS[6]) else TSUB,
                bg=BG3,size=8,bold=True).pack(side="left",pady=9)
            short = desc.split("—")[1].strip() if "—" in desc else desc
            lbl(cell,f"  {short}  ",fg=TSUB,bg=BG3,size=8).pack(side="left",pady=9)

        # 카드 영역
        ct = frm(p, bg=BG); ct.pack(fill="x", padx=24, pady=(18,10))
        lbl(ct,"부품별 시세 & 성능 등급",fg=TXT,bg=BG,size=11,bold=True).pack(side="left")
        lbl(ct,"  중고 기준",fg=TSUB,bg=BG,size=9).pack(side="left",pady=2)

        self._card_grid = frm(p, bg=BG); self._card_grid.pack(fill="x", padx=24)
        for i in range(3): self._card_grid.columnconfigure(i, weight=1)

        # 총계
        tw = frm(p, bg=BG); tw.pack(fill="x", padx=24, pady=(16,0))
        tb = frm(tw, bg=BG3)
        tb.config(highlightbackground=ACC, highlightthickness=1); tb.pack(fill="x")
        ti = frm(tb, bg=BG3); ti.pack(fill="x", padx=24, pady=16)

        tl = frm(ti, bg=BG3); tl.pack(side="left")
        lbl(tl,"예상 총 시세",fg=TSUB,bg=BG3,size=9).pack(anchor="w",pady=(0,6))

        price_row = frm(tl, bg=BG3); price_row.pack(anchor="w")
        for tag, attr in [("최소","_total_min"),("평균","_total_avg"),("최대","_total_max")]:
            cell = frm(price_row, bg=BG3); cell.pack(side="left", padx=(0,24))
            lbl(cell, tag, fg=TSUB, bg=BG3, size=8).pack(anchor="w")
            v = lbl(cell, "—", fg=ACC if tag=="평균" else TMID,
                    bg=BG3, size=14 if tag=="평균" else 11, bold=(tag=="평균"))
            v.pack(anchor="w")
            setattr(self, attr, v)

        lbl(tl,"※ 부품 상태·시장에 따라 ±20% 차이 가능",fg=TSUB,bg=BG3,size=8).pack(anchor="w",pady=(6,0))

        tr = frm(ti, bg=BG3); tr.pack(side="right", anchor="e")
        lbl(tr,"시세 크로스체크",fg=TSUB,bg=BG3,size=8).pack(anchor="e",pady=(0,6))
        br = frm(tr, bg=BG3); br.pack()
        for label,site in [("다나와","danawa"),("네이버쇼핑","naver"),("구글","google")]:
            ghost_btn(br, label, lambda s=site: self._search(s)).pack(side="left",padx=(0,6))

        self._tips(p); self._footer(p)

    # ─────────────────────────────────────────
    #  탭 2 — 최적 조립 추천
    # ─────────────────────────────────────────
    def _build_rec_tab(self, p):
        # 입력 영역
        inp = frm(p, bg=BG2); inp.pack(fill="x")
        ii  = frm(inp, bg=BG2); ii.pack(fill="x", padx=24, pady=20)

        lbl(ii,"예산으로 조립 가능한 최적 구성",fg=TXT,bg=BG2,size=12,bold=True).pack(anchor="w",pady=(0,12))
        lbl(ii,"예산을 입력하면 같은 가격 대비 성능이 가장 높은 CPU+GPU 조합을 찾아드립니다.",
            fg=TSUB,bg=BG2,size=9).pack(anchor="w",pady=(0,12))

        # 입력 행
        row = frm(ii, bg=BG2); row.pack(anchor="w")
        lbl(row,"총 예산  ₩ ",fg=TMID,bg=BG2,size=10).pack(side="left")

        self._budget = tk.StringVar()
        ent = tk.Entry(row, textvariable=self._budget,
                       bg=BG3, fg=TXT, insertbackground=ACC,
                       font=("Segoe UI",11,"bold"), relief="flat", width=13,
                       highlightbackground=BDR2, highlightthickness=1)
        ent.pack(side="left", ipady=7, padx=(0,8))
        lbl(row,"원",fg=TMID,bg=BG2,size=10).pack(side="left",padx=(0,14))

        # 빠른 선택 버튼
        for amt in [30_000, 100_000, 300_000, 500_000, 800_000, 1_000_000, 1_500_000, 2_000_000]:
            ghost_btn(row, f"{amt//10000}만", lambda a=amt: (
                self._budget.set(str(a)), self._run_rec())
            ).pack(side="left", padx=(0,5))

        acc_btn(ii,"최적 구성 찾기", self._run_rec).pack(anchor="w", pady=(12,0))

        sep(p, BDR).pack(fill="x")

        # 결과 영역
        self._rec_area = frm(p, bg=BG); self._rec_area.pack(fill="x", padx=24, pady=20)
        lbl(self._rec_area,
            "스캔을 먼저 실행하면 현재 PC 총 시세가 예산으로 자동 입력됩니다.",
            fg=TSUB, bg=BG, size=9).pack(anchor="w")

        self._footer(p)

    def _run_rec(self):
        raw = self._budget.get().replace(",","").replace("원","").strip()
        clear(self._rec_area)
        if not raw.isdigit():
            lbl(self._rec_area,"숫자만 입력하세요  예)  1000000",fg=RED,bg=BG,size=9).pack(anchor="w")
            return
        budget = int(raw)
        lbl(self._rec_area,"계산 중...",fg=TSUB,bg=BG,size=9).pack(anchor="w")
        threading.Thread(target=lambda: self.root.after(0,lambda: self._show_rec(budget)),
                         daemon=True).start()

    def _show_rec(self, budget):
        clear(self._rec_area)
        p = self._rec_area
        build = recommend_build(budget)

        if not build:
            lbl(p,f"예산 ₩{budget:,}으로는 조립이 어렵습니다.\n가격 DB 최저가 기준 최소 약 ₩95,000 (GTX 1050 Ti + 최소 CPU) 이상이어야 합니다.",
                fg=RED,bg=BG,size=10).pack(anchor="w"); return

        # 헤더
        hr = frm(p, bg=BG); hr.pack(fill="x", pady=(0,4))
        lbl(hr,f"₩{budget:,} 예산  최적 조립 구성",fg=TXT,bg=BG,size=13,bold=True).pack(side="left")
        lc = ACC if build["left"]>=0 else RED
        lt = f"  잔액 ₩{build['left']:,}" if build["left"]>=0 else f"  초과 ₩{abs(build['left']):,}"
        lbl(hr,lt,fg=lc,bg=BG,size=9).pack(side="left",pady=3)

        sr = frm(p, bg=BG); sr.pack(fill="x",pady=(0,14))
        lbl(sr,f"성능 합산 점수  {build['score']:,}점",fg=ACC,bg=BG,size=11,bold=True).pack(side="left")
        lbl(sr,"  (CPU + GPU 점수 합계)",fg=TSUB,bg=BG,size=8).pack(side="left",pady=2)

        sep(p, BDR).pack(fill="x", pady=(0,14))

        # 부품 카드 그리드
        g = frm(p, bg=BG); g.pack(fill="x")
        g.columnconfigure(0, weight=2)
        g.columnconfigure(1, weight=2)
        g.columnconfigure(2, weight=1)

        self._rec_part_card(g,0,0,"CPU",build["cpu"],build["cpu_grade"],build["cpu_p"],ACC)
        self._rec_part_card(g,0,1,"GPU",build["gpu"],build["gpu_grade"],build["gpu_p"],ACCH)

        # 우측 소형 카드들
        rc = frm(g, bg=BG); rc.grid(row=0,column=2,padx=(8,0),sticky="nsew")
        for title,name,price in [
            ("RAM",     build["ram"], build["ram_p"]),
            ("SSD",     build["ssd"], build["ssd_p"]),
            ("기타",    build["etc"], build["etc_p"]),
        ]:
            sc = frm(rc, bg=BG3)
            sc.config(highlightbackground=BDR, highlightthickness=1)
            sc.pack(fill="x", pady=(0,6))
            si = frm(sc, bg=BG3); si.pack(fill="x", padx=12, pady=10)
            rr = frm(si, bg=BG3); rr.pack(fill="x")
            lbl(rr,title,fg=ACC,bg=BG3,size=9,bold=True).pack(side="left")
            lbl(rr,f"  ₩{price:,}",fg=TXT,bg=BG3,size=8).pack(side="left")
            lbl(si,name,fg=TSUB,bg=BG3,size=8).pack(anchor="w")

        # 합계
        sep(p, BDR).pack(fill="x", pady=(14,10))
        totrow = frm(p, bg=BG); totrow.pack(fill="x")
        used = build["cpu_p"]+build["gpu_p"]+build["ram_p"]+build["ssd_p"]+build["etc_p"]
        lbl(totrow,f"총 사용  ₩{used:,}",fg=TXT,bg=BG,size=11,bold=True).pack(side="left")
        lbl(totrow,f"  /  예산  ₩{budget:,}",fg=TSUB,bg=BG,size=9).pack(side="left",pady=2)

        # 다나와 링크
        sep(p, BDR).pack(fill="x", pady=(10,10))
        lr = frm(p, bg=BG); lr.pack(anchor="w")
        lbl(lr,"다나와에서 가격 확인  →  ",fg=TSUB,bg=BG,size=9).pack(side="left")
        for part_name in [build["cpu"], build["gpu"]]:
            enc = urllib.parse.quote(part_name+" 중고 가격")
            url = f"https://search.danawa.com/dsearch.php?query={enc}"
            short = part_name.replace("Core ","").replace("Ryzen ","R")[:22]
            b = tk.Label(lr, text=f"[{short}]  ", bg=BG, fg=ACC,
                         font=("Segoe UI",9,"underline"), cursor="hand2")
            b.pack(side="left")
            b.bind("<Button-1>", lambda e,u=url: webbrowser.open(u))
            b.bind("<Enter>", lambda e,w=b: w.config(fg=ACCH))
            b.bind("<Leave>", lambda e,w=b: w.config(fg=ACC))

    def _rec_part_card(self, parent, row, col, title, name, grade, price, accent):
        outer = frm(parent, bg=BG)
        outer.grid(row=row, column=col, padx=(0 if col==0 else 8, 0), sticky="nsew")
        card = frm(outer, bg=BG3)
        card.config(highlightbackground=BDR, highlightthickness=1); card.pack(fill="both",expand=True)
        inn = frm(card, bg=BG3); inn.pack(fill="both", expand=True, padx=16, pady=14)

        lbl(inn,title,fg=accent,bg=BG3,size=10,bold=True).pack(anchor="w")
        disp = name[:46]+"…" if len(name)>46 else name
        lbl(inn,disp,fg=TXT,bg=BG3,size=9).pack(anchor="w",pady=(4,0))
        sep(inn,BDR).pack(fill="x",pady=8)

        if grade:
            r = grade_dot_row(inn, grade)
            if r: r.pack(fill="x",pady=(0,4))
            lbl(inn,grade["desc"],fg=TSUB,bg=BG3,size=8).pack(anchor="w",pady=(0,6))

        sep(inn,BDR).pack(fill="x",pady=(0,8))
        lbl(inn,f"₩ {price:,}",fg=ACC,bg=BG3,size=13,bold=True).pack(anchor="w")
        lbl(inn,"중고 기준 최저가",fg=TSUB,bg=BG3,size=8).pack(anchor="w")

    # ─────────────────────────────────────────
    #  탭 3 — 부품 비교기
    # ─────────────────────────────────────────
    def _build_compare_tab(self, p):
        inp = frm(p, bg=BG2); inp.pack(fill="x")
        ii  = frm(inp, bg=BG2); ii.pack(fill="x", padx=24, pady=20)

        lbl(ii,"부품 비교기",fg=TXT,bg=BG2,size=12,bold=True).pack(anchor="w",pady=(0,6))
        lbl(ii,"두 부품의 성능 점수·등급·중고 시세를 나란히 비교합니다.\n"
               "예)  RTX 3080  vs  RTX 4070  /  i5-12400  vs  Ryzen 5 5600",
            fg=TSUB,bg=BG2,size=9).pack(anchor="w",pady=(0,14))

        # 입력 행
        row = frm(ii, bg=BG2); row.pack(anchor="w", fill="x")

        # 왼쪽 부품
        lc = frm(row, bg=BG2); lc.pack(side="left")
        lbl(lc,"부품 A",fg=ACC,bg=BG2,size=9,bold=True).pack(anchor="w",pady=(0,4))
        self._cmp_a = tk.StringVar()
        ea = tk.Entry(lc, textvariable=self._cmp_a,
                      bg=BG3, fg=TXT, insertbackground=ACC,
                      font=("Segoe UI",10), relief="flat", width=22,
                      highlightbackground=BDR2, highlightthickness=1)
        ea.pack(ipady=7)
        lbl(lc,"예) RTX 3080  /  i5-12400",fg=TSUB,bg=BG2,size=8).pack(anchor="w",pady=(3,0))

        lbl(row,"   VS   ",fg=TSUB,bg=BG2,size=11,bold=True).pack(side="left",pady=(10,0))

        # 오른쪽 부품
        rc = frm(row, bg=BG2); rc.pack(side="left")
        lbl(rc,"부품 B",fg=ACCH,bg=BG2,size=9,bold=True).pack(anchor="w",pady=(0,4))
        self._cmp_b = tk.StringVar()
        eb = tk.Entry(rc, textvariable=self._cmp_b,
                      bg=BG3, fg=TXT, insertbackground=ACC,
                      font=("Segoe UI",10), relief="flat", width=22,
                      highlightbackground=BDR2, highlightthickness=1)
        eb.pack(ipady=7)
        lbl(rc,"예) RTX 4070  /  Ryzen 5 5600",fg=TSUB,bg=BG2,size=8).pack(anchor="w",pady=(3,0))

        # 부품 종류 선택
        type_row = frm(ii, bg=BG2); type_row.pack(anchor="w", pady=(12,0))
        lbl(type_row,"비교 종류  ",fg=TMID,bg=BG2,size=9).pack(side="left")
        self._cmp_type = tk.StringVar(value="gpu")
        for val,label in [("gpu","GPU"),("cpu","CPU"),("ram","RAM")]:
            rb = tk.Radiobutton(type_row, text=label, variable=self._cmp_type,
                                value=val, bg=BG2, fg=TMID,
                                selectcolor=BG3, activebackground=BG2,
                                activeforeground=ACC,
                                font=("Segoe UI",9), cursor="hand2")
            rb.pack(side="left", padx=(0,12))

        acc_btn(ii,"비교하기", self._run_compare).pack(anchor="w", pady=(12,0))

        # 빠른 비교 예시
        ex_row = frm(ii, bg=BG2); ex_row.pack(anchor="w", pady=(10,0))
        lbl(ex_row,"빠른 비교  ",fg=TSUB,bg=BG2,size=8).pack(side="left")
        for a,b,t,label in [
            ("RTX 3080","RTX 4070","gpu","3080 vs 4070"),
            ("RTX 3060","RTX 3070","gpu","3060 vs 3070"),
            ("i5-12400","Ryzen 5 5600","cpu","i5-12400 vs R5 5600"),
            ("i5-13600K","Ryzen 7 7700X","cpu","13600K vs 7700X"),
        ]:
            ghost_btn(ex_row, label, lambda a=a,b=b,t=t: (
                self._cmp_a.set(a), self._cmp_b.set(b),
                self._cmp_type.set(t), self._run_compare())
            ).pack(side="left", padx=(0,6))

        sep(p, BDR).pack(fill="x")

        self._cmp_result = frm(p, bg=BG)
        self._cmp_result.pack(fill="x", padx=24, pady=20)
        lbl(self._cmp_result,"부품 이름을 입력하고 비교하기를 클릭하세요.\n스캔 후 내 GPU/CPU를 자동으로 불러오려면 스캔을 먼저 실행하세요.",
            fg=TSUB,bg=BG,size=9).pack(anchor="w")

        self._footer(p)

    def _run_compare(self):
        a = self._cmp_a.get().strip()
        b = self._cmp_b.get().strip()
        ctype = self._cmp_type.get()
        clear(self._cmp_result)
        if not a or not b:
            lbl(self._cmp_result,"부품 A와 B를 모두 입력하세요.",fg=RED,bg=BG,size=9).pack(anchor="w")
            return
        self._show_compare(a, b, ctype)

    def _show_compare(self, name_a, name_b, ctype):
        p = self._cmp_result

        sdb = {"gpu": GPU_SCORE, "cpu": CPU_SCORE, "ram": CPU_SCORE}.get(ctype, GPU_SCORE)
        pdb = {"gpu": PRICE_GPU, "cpu": PRICE_CPU, "ram": PRICE_CPU}.get(ctype, PRICE_GPU)

        def lookup(name):
            sc, matched = match_score(name, sdb)
            mn = mx = 0
            for k,(a,b) in pdb.items():
                if name.lower() in k.lower() or k.lower() in name.lower():
                    mn,mx=a,b; break
            year = get_year(name)
            return {"name": name, "matched": matched or name,
                    "score": sc, "grade": get_grade(sc),
                    "min": mn, "max": mx, "year": year}

        da = lookup(name_a)
        db = lookup(name_b)

        # 헤더
        hr = frm(p, bg=BG); hr.pack(fill="x", pady=(0,14))
        lbl(hr,f"{ctype.upper()} 비교  —  {da['matched']}  vs  {db['matched']}",
            fg=TXT,bg=BG,size=12,bold=True).pack(side="left")

        # 카드 2열
        g = frm(p, bg=BG); g.pack(fill="x")
        g.columnconfigure(0, weight=1)
        g.columnconfigure(1, weight=1)

        winner_score = None
        if da["score"] and db["score"]:
            winner_score = "a" if da["score"] > db["score"] else "b" if db["score"] > da["score"] else "tie"

        for side, data, accent, col in [("A", da, ACC, 0), ("B", db, ACCH, 1)]:
            is_winner = (side=="A" and winner_score=="a") or (side=="B" and winner_score=="b")
            border_c = ACC if is_winner else BDR

            outer = frm(g, bg=BG)
            outer.grid(row=0, column=col, padx=(0 if col==0 else 10, 0), sticky="nsew")
            card = frm(outer, bg=BG3)
            card.config(highlightbackground=border_c, highlightthickness=1 if not is_winner else 2)
            card.pack(fill="both", expand=True)
            inn = frm(card, bg=BG3); inn.pack(fill="both", expand=True, padx=18, pady=16)

            # 승자 배지
            title_row = frm(inn, bg=BG3); title_row.pack(fill="x")
            lbl(title_row,f"부품 {side}",fg=accent,bg=BG3,size=9,bold=True).pack(side="left")
            if is_winner:
                lbl(title_row," ★ 우세 ",fg="#000",bg=ACC,size=8,bold=True).pack(side="right")
            elif winner_score=="tie":
                lbl(title_row," = 동점 ",fg=TSUB,bg=BDR2,size=8).pack(side="right")

            lbl(inn,data["matched"],fg=TXT,bg=BG3,size=11,bold=True).pack(anchor="w",pady=(6,0))

            if data["year"]:
                age = datetime.now().year - data["year"]
                ac = RED if age>=5 else TDIM if age>=3 else TMID
                lbl(inn,f"{data['year']}년 출시  ·  {age}년 전",fg=ac,bg=BG3,size=8).pack(anchor="w",pady=(2,0))

            sep(inn,BDR).pack(fill="x",pady=10)

            # 점수
            if data["score"]:
                sc_row = frm(inn, bg=BG3); sc_row.pack(fill="x",pady=(0,4))
                lbl(sc_row,"성능 점수  ",fg=TSUB,bg=BG3,size=9).pack(side="left")
                lbl(sc_row,f"{data['score']:,}",fg=accent,bg=BG3,size=16,bold=True).pack(side="left")
            else:
                lbl(inn,"점수 DB 없음",fg=TSUB,bg=BG3,size=9).pack(anchor="w")

            if data["grade"]:
                r = grade_dot_row(inn, data["grade"])
                if r: r.pack(fill="x",pady=(4,0))
                lbl(inn,data["grade"]["desc"],fg=TSUB,bg=BG3,size=8).pack(anchor="w",pady=(2,8))

            sep(inn,BDR).pack(fill="x",pady=(0,10))

            if data["min"] > 0:
                lbl(inn,f"₩{data['min']:,}  ~  ₩{data['max']:,}",fg=ACC,bg=BG3,size=12,bold=True).pack(anchor="w")
                lbl(inn,"중고 시세 기준",fg=TSUB,bg=BG3,size=8).pack(anchor="w")
            else:
                lbl(inn,"가격 DB 없음",fg=TSUB,bg=BG3,size=9).pack(anchor="w")

        # 차이 요약
        if da["score"] and db["score"]:
            sep(p, BDR).pack(fill="x", pady=(16,12))
            diff = abs(da["score"] - db["score"])
            pct  = round(diff / min(da["score"],db["score"]) * 100)
            stronger = da["matched"] if da["score"] > db["score"] else db["matched"]

            summary = frm(p, bg=BG2)
            summary.config(highlightbackground=ACC, highlightthickness=1)
            summary.pack(fill="x")
            si = frm(summary, bg=BG2); si.pack(fill="x", padx=20, pady=14)

            if winner_score == "tie":
                lbl(si,"두 부품의 성능이 동일합니다. 가격이 더 저렴한 쪽이 유리합니다.",
                    fg=TXT,bg=BG2,size=10).pack(anchor="w")
            else:
                lbl(si,f"{stronger}  이(가) 성능 점수 기준  {pct}%  더 우세합니다.",
                    fg=TXT,bg=BG2,size=10,bold=True).pack(anchor="w")

            if da["min"]>0 and db["min"]>0:
                price_diff = abs(da["min"] - db["min"])
                cheaper = da["matched"] if da["min"] < db["min"] else db["matched"]
                lbl(si,f"가격은 {cheaper}이(가) 중고 기준 약 ₩{price_diff:,} 더 저렴합니다.",
                    fg=TSUB,bg=BG2,size=9).pack(anchor="w",pady=(4,0))

    # ─────────────────────────────────────────
    #  탭 4 — 내 PC 보고서
    # ─────────────────────────────────────────
    def _build_report_tab(self, p):
        inp = frm(p, bg=BG2); inp.pack(fill="x")
        ii  = frm(inp, bg=BG2); ii.pack(fill="x", padx=24, pady=20)

        lbl(ii,"내 PC 보고서",fg=TXT,bg=BG2,size=12,bold=True).pack(anchor="w",pady=(0,6))
        lbl(ii,"스캔 결과를 텍스트로 정리합니다. 수리점 방문 전 카카오톡/메모장에 붙여넣기 하세요.",
            fg=TSUB,bg=BG2,size=9).pack(anchor="w",pady=(0,14))

        btn_row = frm(ii, bg=BG2); btn_row.pack(anchor="w")
        acc_btn(btn_row,"보고서 생성",self._gen_report).pack(side="left")
        ghost_btn(btn_row,"클립보드 복사",self._copy_report).pack(side="left",padx=(10,0))

        sep(p, BDR).pack(fill="x")

        self._report_area = frm(p, bg=BG)
        self._report_area.pack(fill="x", padx=24, pady=20)
        lbl(self._report_area,"스캔을 먼저 실행한 후 보고서를 생성하세요.",
            fg=TSUB,bg=BG,size=9).pack(anchor="w")

        self._footer(p)

    def _build_report_text(self):
        hw = self.hw; pr = self.prices
        now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
        lines = []
        lines.append("=" * 52)
        lines.append("  프라임세이지 돌팔이체커 — PC 분석 보고서")
        lines.append(f"  생성일시  {now}")
        lines.append("=" * 52)
        lines.append("")

        lines.append("[ 시스템 정보 ]")
        lines.append(f"  OS         {hw.get('os','알 수 없음')}")
        lines.append(f"  CPU        {hw.get('cpu','알 수 없음')}")
        lines.append(f"  GPU        {hw.get('gpu','알 수 없음')}")
        lines.append(f"  RAM        {hw.get('ram','알 수 없음')}")
        stor = " / ".join(hw.get("storage",[])) or "알 수 없음"
        lines.append(f"  스토리지   {stor}")
        lines.append(f"  메인보드   {hw.get('motherboard','알 수 없음')}")
        lines.append("")

        lines.append("[ 부품별 등급 & 시세 ]")
        for key, label in [("cpu","CPU"),("gpu","GPU"),("ram","RAM"),
                           ("storage","스토리지"),("misc","기타")]:
            d = pr.get(key,{})
            name = d.get("detail") or d.get("name","알 수 없음")
            grade = d.get("grade")
            g_str = f"{grade['name']} (점수 {grade['score']})" if grade else "—"
            mn,mx = d.get("min",0), d.get("max",0)
            p_str = f"₩{mn:,} ~ ₩{mx:,}" if mn>0 else "DB 없음"
            year = d.get("year")
            y_str = f"  ({year}년 출시)" if year else ""
            lines.append(f"  {label:<6}  {name[:30]}{y_str}")
            lines.append(f"          등급: {g_str}  /  시세: {p_str}")

        lines.append("")
        t = pr.get("total",{})
        mn,mx = t.get("min",0), t.get("max",0)
        lines.append("[ 예상 총 시세 ]")
        if mn > 0:
            lines.append(f"  ₩{mn:,}  ~  ₩{mx:,}  (중고 기준)")
        else:
            lines.append("  데이터 부족 — 직접 검색 권장")

        lines.append("")
        lines.append("[ 돌팔이 방지 체크리스트 ]")
        lines.append("  □ 수리비가 부품 시세 범위 안에 있는가?")
        lines.append("  □ 교체 전후 부품 사진을 받았는가?")
        lines.append("  □ 부품 등급 대비 과도한 비용 청구는 아닌가?")
        lines.append("  □ 중고나라·번개장터 시세와 교차 확인했는가?")
        lines.append("")
        lines.append("  ※ 본 보고서는 참고용이며 실제 시세와 다를 수 있습니다.")
        lines.append("  프라임세이지 돌팔이체커")
        lines.append("=" * 52)
        return "\n".join(lines)

    def _gen_report(self):
        if not self.prices:
            clear(self._report_area)
            lbl(self._report_area,"스캔을 먼저 실행하세요.",fg=RED,bg=BG,size=9).pack(anchor="w")
            return
        clear(self._report_area)
        p = self._report_area
        text = self._build_report_text()

        # 텍스트 박스
        txt_wrap = frm(p, bg=BG3)
        txt_wrap.config(highlightbackground=BDR, highlightthickness=1)
        txt_wrap.pack(fill="x")

        txt = tk.Text(txt_wrap, bg=BG3, fg=TXT,
                      font=("Courier New", 9),
                      relief="flat", padx=16, pady=14,
                      insertbackground=ACC, height=26,
                      selectbackground=BDR2, selectforeground=TXT)
        vsb = tk.Scrollbar(txt_wrap, orient="vertical", command=txt.yview,
                           bg=BG2, troughcolor=BG2)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        txt.insert("1.0", text)
        txt.config(state="disabled")
        self._report_text = text
        self._report_widget = txt

        # 하단 버튼
        btn_row = frm(p, bg=BG); btn_row.pack(anchor="w", pady=(12,0))
        acc_btn(btn_row,"클립보드 복사",self._copy_report,small=True).pack(side="left")
        self._copy_notice = lbl(btn_row,"",fg=ACC,bg=BG,size=9)
        self._copy_notice.pack(side="left", padx=(12,0))

    def _copy_report(self):
        if not hasattr(self,"_report_text") or not self._report_text:
            if not self.prices:
                return
            self._report_text = self._build_report_text()
        self.root.clipboard_clear()
        self.root.clipboard_append(self._report_text)
        self.root.update()
        if hasattr(self,"_copy_notice"):
            self._copy_notice.config(text="✓ 클립보드에 복사됐습니다!")
            self.root.after(2500, lambda: self._copy_notice.config(text=""))

    def _tips(self, parent):
        tw = frm(parent, bg=BG); tw.pack(fill="x", padx=24, pady=(18,0))
        tb = frm(tw, bg=BG3)
        tb.config(highlightbackground=BDR, highlightthickness=1); tb.pack(fill="x")
        ti = frm(tb, bg=BG3); ti.pack(fill="x", padx=24, pady=14)
        lbl(ti,"돌팔이 방지 팁",fg=ACC,bg=BG3,size=10,bold=True).pack(anchor="w",pady=(0,8))
        for i,tip in enumerate([
            "LOWER 이하 부품에 수십만원 수리비를 청구하면 즉시 의심하세요.",
            "부품 교체를 주장할 경우, 교체 전후 사진을 반드시 요구하세요.",
            "RAM·SSD 등급이 낮다며 업그레이드 강권 → 과잉 정비 가능성.",
            "이 앱의 가격 범위 확인 후 중고나라·번개장터에서도 크로스체크하세요.",
            "출시 연도가 오래될수록 감가를 충분히 고려하고 '최신 부품' 주장은 검증하세요.",
        ],1):
            r = frm(ti, bg=BG3); r.pack(fill="x", pady=2)
            lbl(r,f"{i:02d}",fg=ACC,bg=BG3,size=8,bold=True).pack(side="left")
            lbl(r,f"  {tip}",fg=TMID,bg=BG3,size=9).pack(side="left")

    def _footer(self, parent):
        sep(parent, BDR).pack(fill="x", pady=(16,0))
        lbl(parent,"© 2025 프라임세이지 돌팔이체커  —  부품 시세는 참고용이며 실제와 다를 수 있습니다.",
            fg=TSUB, bg=BG, size=8).pack(pady=12)

    # ─────────────────────────────────────────
    #  스캔 실행
    # ─────────────────────────────────────────
    def scan(self):
        self._status.set("하드웨어 감지 중...")
        self._anim_i = 0
        self._pulse()
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _pulse(self):
        colors = [ACC, ACCH, "#FFFFFF", ACCH]
        self._dot.config(bg=colors[self._anim_i % 4])
        self._anim_i += 1
        self._anim_id = self.root.after(500, self._pulse)

    def _do_scan(self):
        self.hw = detect_hw()
        self.root.after(0, lambda: self._status.set("시세 조회 중..."))
        self.prices = estimate_prices(self.hw)
        self.root.after(0, self._apply)

    def _apply(self):
        if self._anim_id:
            self.root.after_cancel(self._anim_id); self._anim_id = None
        self._dot.config(bg=ACC)
        self._status.set(f"스캔 완료  ·  {datetime.now().strftime('%Y.%m.%d %H:%M:%S')}")

        hw = self.hw
        stor = ", ".join(hw.get("storage",[])) or "알 수 없음"
        self._hw_os.config(text=hw.get("os",""))
        for key, val in [("CPU",hw.get("cpu","알 수 없음")),
                         ("GPU",hw.get("gpu","알 수 없음")),
                         ("RAM",hw.get("ram","알 수 없음")),
                         ("STORAGE",stor),
                         ("MOTHERBOARD",hw.get("motherboard","알 수 없음"))]:
            v = val[:32]+"…" if len(val)>32 else val
            self._hw_lbls[key].config(text=v)

        # 카드 재렌더
        clear(self._card_grid)
        for r in range(2): self._card_grid.rowconfigure(r, weight=1)
        LAYOUT=[("cpu",0,0),("gpu",0,1),("ram",0,2),("storage",1,0),("misc",1,1)]
        for key,row,col in LAYOUT:
            data = self.prices.get(key,{})
            self._part_card(self._card_grid, row, col, key.upper(), data,
                            PART_ACC.get(key, BDR2))

        t = self.prices.get("total",{})
        mn,mx = t.get("min",0), t.get("max",0)
        if mn > 0:
            avg = (mn + mx) // 2
            self._total_min.config(text=f"₩{mn:,}")
            self._total_avg.config(text=f"₩{avg:,}")
            self._total_max.config(text=f"₩{mx:,}")
        else:
            self._total_min.config(text="—")
            self._total_avg.config(text="데이터 부족")
            self._total_max.config(text="—")

        # 추천 탭 예산 자동 입력
        if mn > 0:
            self._budget.set(str((mn+mx)//2))

        # 비교 탭 — 내 GPU/CPU 자동 입력
        my_gpu = hw.get("gpu","")
        my_cpu = hw.get("cpu","")
        if my_gpu and my_gpu != "알 수 없음":
            self._cmp_a.set(my_gpu)
            self._cmp_type.set("gpu")
        elif my_cpu and my_cpu != "알 수 없음":
            self._cmp_a.set(my_cpu)
            self._cmp_type.set("cpu")

    def _part_card(self, parent, row, col, label, data, accent):
        outer = frm(parent, bg=BG)
        outer.grid(row=row, column=col,
                   padx=(0 if col==0 else 6, 0), pady=5, sticky="nsew")

        card = frm(outer, bg=BG3)
        card.config(highlightbackground=BDR, highlightthickness=1)
        card.pack(fill="both", expand=True)
        inn = frm(card, bg=BG3); inn.pack(fill="both", expand=True, padx=16, pady=14)

        # 헤더
        hr = frm(inn, bg=BG3); hr.pack(fill="x")
        lbl(hr,label,fg=accent,bg=BG3,size=10,bold=True).pack(side="left")
        if data.get("web_used"):
            lbl(hr," 웹검색 ",fg=TSUB,bg=BG3,size=7).pack(side="right")

        # 모델명
        name = data.get("detail") or data.get("name","알 수 없음")
        disp = name[:46]+"…" if len(name)>46 else name
        lbl(inn,disp,fg=TXT,bg=BG3,size=9).pack(anchor="w",pady=(4,0))

        # 연도
        year = data.get("year")
        if year:
            age = datetime.now().year-year
            ac = RED if age>=5 else TDIM if age>=3 else TMID
            lbl(inn,f"{year}년 출시  ·  {age}년 전",fg=ac,bg=BG3,size=8).pack(anchor="w",pady=(2,0))

        sep(inn,BDR).pack(fill="x",pady=8)

        # 등급
        grade = data.get("grade")
        if grade:
            r = grade_dot_row(inn, grade)
            if r: r.pack(fill="x",pady=(0,4))
            lbl(inn,grade["desc"],fg=TSUB,bg=BG3,size=8).pack(anchor="w",pady=(0,6))
        else:
            frm(inn,bg=BG3,height=4).pack()

        sep(inn,BDR).pack(fill="x",pady=(0,8))

        # 가격
        mn,mx = data.get("min",0), data.get("max",0)
        if mn>0:
            avg = (mn+mx)//2
            pr = frm(inn,bg=BG3); pr.pack(fill="x")
            for tag,val,is_main in [("최소",mn,False),("평균",avg,True),("최대",mx,False)]:
                cell = frm(pr,bg=BG3); cell.pack(side="left",padx=(0,14))
                lbl(cell,tag,fg=TSUB,bg=BG3,size=7).pack(anchor="w")
                lbl(cell,f"₩{val:,}",
                    fg=ACC if is_main else TMID,
                    bg=BG3,size=11 if is_main else 9,
                    bold=is_main).pack(anchor="w")
        else:
            lbl(inn,"가격 DB 없음",fg=TSUB,bg=BG3,size=10).pack(anchor="w")
            raw_name = data.get("name","")
            if raw_name not in ("알 수 없음","","케이스 / 파워 / 메인보드 / 쿨러",None):
                enc = urllib.parse.quote(raw_name+" 중고 가격")
                lr = frm(inn,bg=BG3); lr.pack(anchor="w",pady=(4,0))
                for t,url in [
                    ("다나와",f"https://search.danawa.com/dsearch.php?query={enc}"),
                    ("구글",  f"https://www.google.com/search?q={enc}"),
                ]:
                    b = tk.Label(lr,text=t+"  ",bg=BG3,fg=ACC,
                                 font=("Segoe UI",8,"underline"),cursor="hand2")
                    b.pack(side="left")
                    b.bind("<Button-1>",lambda e,u=url: webbrowser.open(u))
                    b.bind("<Enter>",lambda e,w=b: w.config(fg=ACCH))
                    b.bind("<Leave>",lambda e,w=b: w.config(fg=ACC))

        frm(inn,bg=BG3,height=2).pack()

    # ─────────────────────────────────────────
    def _search(self, site):
        q = self.hw.get("cpu","") or self.hw.get("gpu","") or "PC 부품 시세"
        for db in (PRICE_CPU, PRICE_GPU):
            for name in db:
                if name.lower() in q.lower(): q=name; break
        enc = urllib.parse.quote(q+" 중고 가격")
        webbrowser.open({
            "danawa":f"https://search.danawa.com/dsearch.php?query={enc}",
            "naver": f"https://search.shopping.naver.com/search/all?query={enc}",
            "google":f"https://www.google.com/search?q={enc}",
        }[site])

if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(True, True)

    # 아이콘 적용
    import os
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass  # 아이콘 오류 시 기본 아이콘 유지

    App(root)
    root.mainloop()