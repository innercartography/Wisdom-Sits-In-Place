import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow, Polygon
import math, sys
out = sys.argv[1]
fig, ax = plt.subplots(figsize=(9, 14), dpi=150)
fig.patch.set_facecolor("#0b1440"); ax.set_facecolor("#7a1d12")
def rect(x0,x1,z0,z1,fc,ec="none",label=None,lc="white",fs=8,alpha=1,ls="-"):
    ax.add_patch(Rectangle((x0,z0),x1-x0,z1-z0,fc=fc,ec=ec,alpha=alpha,lw=1.2,ls=ls))
    if label: ax.text((x0+x1)/2,(z0+z1)/2,label,ha="center",va="center",color=lc,fontsize=fs,weight="bold")
# sea + deck
rect(-14,36,-60,72,"#b9d6d0",label=None)                       # main causeway deck
ax.text(30,-50,"TILED CAUSEWAY\n(pale cyan tile grid)",color="#123",fontsize=8,ha="center")
rect(-6,6,72,98,"#b9d6d0")                                      # walkways continue
rect(-12,12,98,122,"#d8ece8",ec="#123")
ax.text(0,117,"LIGHTNING PLATFORM",ha="center",color="#123",fontsize=8,weight="bold")
rect(-2,1,6,98,"#0a0f2a",label="",lc="white")                   # channel
ax.text(-0.5,52,"CHANNEL\n+ ribbon\nstair",color="white",fontsize=6.5,ha="center",rotation=90,va="center")
rect(2,14,30,60,"#9fc3cf",ec="#123",label=None)                 # plinth
ax.text(4.5,45,"PLINTH\n+pool",color="#123",fontsize=6.5,ha="center",rotation=90)
rect(6,12,48,56,"#2c47c9",ec="white",label="TOWER\n45m",fs=6.5)
rect(12,16,17,40,"#4d7cff",ec="white",label="GLASS\nMONO-\nLITH\n70m",fs=6.5)
ax.add_patch(Polygon([(16,40),(16,17),(4,10),(2,26)],fc="#8a4a3a",ec="#e8b",alpha=.45,ls="--"))
ax.text(7,16,"LINTEL\n(overhead,\n~55m up)",color="#ffd9c8",fontsize=6.5,ha="center")
rect(26,30,-5,30,"#151a3a",ec="#7aa",label="STAR-\nFIELD\nMONO-\nLITH\n60m",fs=6.5)
for (x,z,n) in [(-8,10,"bent\ntree"),(7,38,"plinth\ntree")]:
    ax.add_patch(plt.Circle((x,z),2.4,fc="#1f3d1a",ec="#9c6"))
    ax.text(x+3.4 if x>0 else x,z if x>0 else z-4.5,n.replace("\n"," ") if x<0 else n,color="#0f240c",fontsize=6.5,ha="left" if x>0 else "center",va="center",weight="bold")
rect(-12,-8,-58,-54,"#4d7cff",ec="white"); rect(8,12,-58,-54,"#4d7cff",ec="white")
ax.text(0,-56,"SOUTH GATE\n(~180m south,\nshown compressed)",color="#123",fontsize=6.5,ha="center",va="center")
# sun
ax.annotate("SUN on horizon\n(azimuth ~355°)\n+ red sea haze",xy=(-6,135),color="#ffcc66",fontsize=8,ha="center")
ax.plot([0,-8],[0,135],color="#ffcc66",lw=.8,ls=":")
# stations
st = {"A":(0,0),"B":(4,34),"C":(-0.5,22),"D":(9,22),"E":(0,108)}
for k,(x,z) in st.items():
    for yaw,c in [(0,"#ff3b30"),(90,"#ffcc00"),(180,"#34c759"),(270,"#5ac8fa")]:
        dx,dz = 3.6*math.sin(math.radians(yaw)),3.6*math.cos(math.radians(yaw))
        ax.add_patch(FancyArrow(x,z,dx,dz,width=.35,head_width=1.3,head_length=1.1,color=c,length_includes_head=True))
    ax.add_patch(plt.Circle((x,z),1.1,fc="white",ec="black",zorder=5))
    ax.text(x,z,k,ha="center",va="center",fontsize=8,weight="bold",zorder=6)
# A0 frustum
for a in (-45,45):
    ax.plot([0,60*math.sin(math.radians(a))],[0,60*math.cos(math.radians(a))],color="white",lw=.7,ls="--",alpha=.7)
ax.text(-16.5,48,"A0 = source\nframe\n(~90° FOV)",color="white",fontsize=7,ha="center")
ax.set_xlim(-22,40); ax.set_ylim(-62,142); ax.set_aspect("equal")
ax.set_xlabel("x  (metres, + = east / right of source view)",color="white"); ax.set_ylabel("z  (metres, + = north / into the source view)",color="white")
ax.tick_params(colors="white"); ax.grid(color="white",alpha=.12)
ax.set_title("STORM TERRACE — site plan (top-down, north up)\narrows: red=Front 0°  yellow=Right 90°  green=Back 180°  blue=Left 270°",color="white",fontsize=10)
plt.tight_layout(); plt.savefig(out, facecolor=fig.get_facecolor())
