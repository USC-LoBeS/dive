import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os 

nifti_li, track_li,vtk_li = [], [], []
ouptput_file_name = []
width_value = 1
zoom_value = 0.5
command = ""
def nifti():
    global nifti_li
    filename = filedialog.askopenfilenames(initialdir = os.getcwd(),title = "Select Nifti Files",multiple=True, filetypes = (("Nifti files", "*.nii.*"),("Compressed","*.gz"),("all files","*.*")))
    if filename:
        nifti_li = list(filename)
    else:
        nifti_li = None

def track():
    global track_li
    filename = filedialog.askopenfilenames(initialdir = os.getcwd(),title = "Select Tracks Files",multiple=True, filetypes = (("Trk files", "*.trk"),("Tck files", "*.tck"),("Trx files", "*.trx"),("all files","*.*")))
    if filename:
        track_li = list(filename)
    else:
        return None

def vtk():
    global vtk_li
    filename = filedialog.askopenfilenames(initialdir = os.getcwd(),title = "Select Tracks Files",multiple=True, filetypes = (("Vtk files", "*.vtk"),("all files","*.*")))
    if filename:
        vtk_li = list(filename)
    else:
        return None
background_val = 0
def width_control(value2):
    global width_value
    value_label_track.config(text=f"Track Width: {value2}")
    width_value = value2

def choose_output_path():
    global ouptput_file_name
    filename = filedialog.asksaveasfilename(defaultextension=".png",title="Save As" )
    if filename:
        ouptput_file_name = filename
    else:
        return None

mask_csv_val,tract_csv_val = [],[]
## CSV functions
def csv_mask():
    global mask_csv_val
    filename = filedialog.askopenfilenames(initialdir = "/",title = "Select CSV Files",multiple=True, filetypes = (("CSV files", "*.csv"),("all files","*.*")))
    if filename:
        mask_csv_val = list(filename)
    else:
        mask_csv_val = None

def csv_track():
    global tract_csv_val
    filename = filedialog.askopenfilenames(initialdir = "/",title = "Select CSV Files",multiple=True, filetypes = (("CSV files", "*.csv"),("all files","*.*")))
    if filename:
        tract_csv_val = list(filename)
    else:
        tract_csv_val = None

def p_val():
    if var_log_pval.get() == 1:
        label_pval.config(text="Do log for pval")
    else:
        label_pval.config(text="Don't apply")
def submit():
    global command
    global nifti_li,track_li,vtk_li,ouptput_file_name,mask_csv_val,tract_csv_val,threshold_tract
    global threshold_mask,var_log_pval,zoom_value,width_value
    global tvalue_range, pvalue_range, map_pval_value_val, map_tval_value_val
    global color_mask_value_val,color_tract_value_val,color_vtk_value_val
    global background_val
    if len(vtk_li)>0:
        command+= " --mesh " + " ".join(vtk_li)
    if len(nifti_li)>0:
        command+= " --mask " + " ".join(nifti_li)
    if len(track_li)>0:
        command+= " --tract " + " ".join(track_li)
    if len(mask_csv_val)>0:
        command+= " --stats_csv " + " ".join(mask_csv_val)
    if threshold_mask.get():
        command+= " --threshold " + str(threshold_mask.get())
    if width_value:
        command+= " --width_tract " + str(width_value)
    if var_log_pval.get():
        command+= " --log_p_value " + str(var_log_pval.get())
    if str(pvalue_range.get())!="(Min,Max)":
        command+= " --range_value "+ str(pvalue_range.get()).replace(",", " ")
    if map_pval_value.get():
        command+= " --map "+ str(map_pval_value_val.get())
    if color_mask_value.get():
        command+= " --color_mask "+ str(color_mask_value_val.get())
    if color_vtk_value.get():
        command+= " --color_mesh "+ str(color_vtk_value_val.get())
    if color_tract_value.get():
        command+= " --color_tract "+ str(color_tract_value_val.get())

    #  command
    print(command)
    window.destroy()



window = tk.Tk()
window.title("DiVE")
window.geometry('400x600')

title = ttk.Label(master = window, text="Input Files",font='Arial 15 bold')
title.pack()

input_frame = ttk.Frame(master=window)
mask = ttk.Button(input_frame,text='Add Mask',command=nifti)
track_button = ttk.Button(input_frame,text='Add Tract',command=track)
vtk_button = ttk.Button(input_frame,text="Add Mesh",command=vtk)

mask.grid(row=0, column=0)
track_button.grid(row=0, column=1)
vtk_button.grid(row=0, column=2)
input_frame.pack(pady=10)

input_frame2 = ttk.Frame(master=window)

value_label_track = tk.Label(input_frame2, text="Track Width: 1",fg="blue")
width_slider = tk.Scale(input_frame2, from_=1, to=15,  orient="horizontal", command=width_control)
width_slider.set(1) 
width_slider.grid(row=4, column=0, padx=1, pady=1)
value_label_track.grid(row=4, column=1, padx=1, pady=1)


input_frame2.pack(pady=10)

title3 = ttk.Label(master = window, text="Visualize with Stats",font='Arial 15 bold')
title3.pack()
input_frame3 = ttk.Frame(master=window)

mask_csv = ttk.Button(input_frame3,text='Add CSV for Mask',command=csv_mask)
mask_csv.grid(row=0, column=0, padx=1, pady=1)


threshold_label = ttk.Label(input_frame3, text="Threshold Value:")
threshold_label.grid(row=1, column=0, padx=1, pady=1, sticky="w")
threshold_mask=tk.DoubleVar()
threshold_entry = ttk.Entry(input_frame3,textvariable=threshold_mask)
threshold_entry.grid(row=1, column=1, padx=1, pady=1)


var_log_pval = tk.IntVar() 
checkbox_pval = tk.Checkbutton(input_frame3, text="Apply Log for P value", variable=var_log_pval, command=p_val)
label_pval = tk.Label(input_frame3, text=" Default Don't apply", fg="blue")

checkbox_pval.grid(row=3, column=0, padx=1, pady=1)
label_pval.grid(row=3, column=1, padx=1, pady=1)

pvalue_r = ttk.Label(input_frame3, text=" Pvalue Range(Min,Max):")
pvalue_r.grid(row=4, column=0, padx=1, pady=1, sticky="w")
pvalue_range=tk.StringVar()
pvalue_range_entry = ttk.Entry(input_frame3,textvariable=pvalue_range)
pvalue_range_entry.insert(0, "(Min,Max)") 
pvalue_range_entry.grid(row=4, column=1, padx=1, pady=1)

map_pval = ttk.Label(input_frame3, text="Color Map for Value")
map_pval.grid(row=5, column=0, padx=1, pady=1, sticky="w")
map_pval_value_val=tk.StringVar()
map_pval_value = ttk.Entry(input_frame3,textvariable=map_pval_value_val)
map_pval_value.insert(0, "RdBu") 
map_pval_value.grid(row=5, column=1, padx=1, pady=1)

input_frame3.pack(pady=10)

##Colors
title4 = ttk.Label(master = window, text="Add Colors",font='Arial 15 bold')
title4.pack()
input_frame4 = ttk.Frame(master=window)

color_mask = ttk.Label(input_frame4, text="Mask Colors")
color_mask.grid(row=0, column=0, padx=1, pady=1, sticky="w")
color_mask_value_val=tk.StringVar()
color_mask_value = ttk.Entry(input_frame4,textvariable=color_mask_value_val)
color_mask_value.grid(row=0, column=1, padx=1, pady=1)

color_tract = ttk.Label(input_frame4, text="Tract Colors")
color_tract.grid(row=1, column=0, padx=1, pady=1, sticky="w")
color_tract_value_val=tk.StringVar()
color_tract_value = ttk.Entry(input_frame4,textvariable=color_tract_value_val)
color_tract_value.grid(row=1, column=1, padx=1, pady=1)

color_vtk = ttk.Label(input_frame4, text="Mesh Colors")
color_vtk.grid(row=2, column=0, padx=1, pady=1, sticky="w")
color_vtk_value_val=tk.StringVar()
color_vtk_value = ttk.Entry(input_frame4,textvariable=color_vtk_value_val)
color_vtk_value.grid(row=2, column=1, padx=1, pady=1)



input_frame4.pack(pady=10)
submit_button = ttk.Button(window,text='Submit',command=submit)
submit_button.pack()
window.mainloop()


