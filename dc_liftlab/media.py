"""Publication figures and a 60 second simulation replay."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

COLORS=['#e8ab60','#33bda6','#b789ec']
def generate(traces,metrics,qrows,out,p):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,2,figsize=(12,7),layout='constrained')
    for (mode,rows),color in zip(traces.items(),COLORS):
        t=[r['time_s'] for r in rows]
        for ax,key,label in zip(axs.flat,['speed_rad_s','bus_V','grid_W','resistor_W'],['Shaft speed (rad/s)','DC bus (V)','Source power, excluding field (W)','Brake resistor power (W)']):
            ax.plot(t,[r[key] for r in rows],color=color,label=mode.replace('_',' '));ax.set_ylabel(label);ax.set_xlabel('Time (s)');ax.grid(alpha=.2)
    axs[0,0].plot(t,[r['reference_rad_s'] for r in rows],':',color='black',label='reference')
    axs[0,1].legend(fontsize=8);fig.suptitle('DC LiftLab | Matched duty cycles, three energy paths',fontsize=16)
    fig.savefig(out/'comparison.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained')
    x=list(range(3));ax.bar(x,[m['net_imported_Wh'] for m in metrics],color=COLORS)
    ax.set_xticks(x,[m['mode'].replace('_',' ').title() for m in metrics]);ax.set_ylabel('Net source energy (Wh), including field')
    for j,m in enumerate(metrics):ax.text(j,m['net_imported_Wh']+.1,f"{m['net_imported_Wh']:.2f} Wh",ha='center')
    ax.set_ylim(0,12);ax.set_title('Same load, motion profile and control settings\nIllustrative simulation; not hardware measurements')
    fig.savefig(out/'energy_comparison.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,5),layout='constrained');ax.plot([r['speed_rad_s'] for r in qrows],[r['torque_Nm'] for r in qrows],color='#247f91');ax.axhline(0,color='gray',lw=.7);ax.axvline(0,color='gray',lw=.7);ax.set_xlabel('Speed (rad/s)');ax.set_ylabel('Electromagnetic torque (N m)');ax.set_title('Independent inertial-load reversal benchmark');fig.savefig(out/'four_quadrants.png',dpi=180);plt.close(fig)
    # Energy audit includes stored-energy change; do not force a closed-cycle equality.
    m=metrics[1];row=traces['regenerative'][-1]
    stored=m['net_imported_Wh']-m['other_losses_Wh']-m['resistor_Wh']-m['brake_Wh']-m['energy_residual_J']/3600
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    labels=['Net input','Losses','Resistor','Mechanical brake','Stored change','Residual']
    vals=[m['net_imported_Wh'],m['other_losses_Wh'],m['resistor_Wh'],m['brake_Wh'],stored,m['energy_residual_J']/3600]
    ax.bar(labels,vals,color=['#247f91']+['#33bda6']*4+['#e8ab60']);ax.set_ylabel('Energy (Wh)');ax.set_title('Regenerative cycle energy audit');ax.tick_params(axis='x',labelrotation=15);fig.savefig(out/'energy_audit.png',dpi=180);plt.close(fig)
    font_path=Path('C:/Windows/Fonts/segoeui.ttf')
    def font(size):
        return ImageFont.truetype(str(font_path),size) if font_path.exists() else ImageFont.load_default(size=size)
    frames=[]; rows=traces['export_loss']
    for j in range(180):
        r=rows[round(j*(len(rows)-1)/179)]
        im=Image.new('RGB',(1280,720),'#091521');d=ImageDraw.Draw(im)
        d.text((48,28),'DC LiftLab',font=font(40),fill='#eff5fa');d.text((48,85),'Regenerative hoist drive | Virtual test bench',font=font(22),fill='#9db0c2')
        d.text((48,136),f"SIMULATION TIME  {r['time_s']:05.2f} s",font=font(20),fill='#48ddbd')
        d.line([(100,590),(100,215),(470,215)],fill='#4c6a80',width=12)
        y=550-max(0,r['height_m'])/5*245
        d.line([(335,215),(335,y)],fill='white',width=3)
        d.rounded_rectangle((275,y,395,y+55),8,fill='#ffbd69' if r['resistor_W']>100 else '#48ddbd')
        d.text((284,y+12),f'{p.mass:g} kg',font=font(22),fill='#091521')
        for k,(label,value) in enumerate([('DC BUS',f"{r['bus_V']:.1f} V"),('ARMATURE CURRENT',f"{r['current_A']:.1f} A"),('RETURNED ENERGY',f"{r['exported_Wh']:.2f} Wh"),('BRAKE RESISTOR',f"{r['resistor_W']:.0f} W")]):
            xx=570+(k%2)*320;yy=180+(k//2)*140
            d.rounded_rectangle((xx,yy,xx+290,yy+115),12,fill='#132b3c');d.text((xx+18,yy+14),label,font=font(16),fill='#9db0c2');d.text((xx+18,yy+46),value,font=font(34),fill='white')
        message='Holding load' if r['state']=='HOLDING' else ('Source export unavailable: brake chopper absorbs energy' if r['time_s']>=20 and r['resistor_W']>20 else ('Lowering: mechanical energy returns to source' if r['grid_W']<0 else 'Lifting: electrical energy raises the load'))
        d.text((48,627),message,font=font(24),fill='#48ddbd');d.text((48,678),'Illustrative parameters | Averaged converters | No hardware validation',font=font(17),fill='#9db0c2')
        d.text((570,505),r['state'],font=font(26),fill='#ffbd69');d.text((570,554),f"Load height: {r['height_m']:.2f} m",font=font(22),fill='white')
        frames.append(im)
    frames[0].save(out/'demo.gif',save_all=True,append_images=frames[1:],duration=333,loop=0,optimize=False)
    try:
        import imageio_ffmpeg
        writer=imageio_ffmpeg.write_frames(str(out/'demo.mp4'),(1280,720),fps=3,codec='libx264',quality=8,macro_block_size=1)
        writer.send(None)
        for frame in frames:writer.send(frame.tobytes())
        writer.close()
    except ImportError:
        pass
