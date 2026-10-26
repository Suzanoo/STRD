"""Native Tk/ttk pilot. Widgets adapt drafts/results; all strengths come from A2."""
import json
import tkinter as tk
from tkinter import ttk, messagebox
from .model import MemberSession, FLAGS, DraftError


class StrengthApp:
    def __init__(self, root, session=None):
        self.root = root
        self.session = session or MemberSession()
        self.loading = False
        self.ci = self.si = 0
        self.vars = {}
        self.widgets = {}
        root.title('STRD - H-beam strength checker | P1 pilot')
        root.geometry('1180x820'); root.minsize(960, 700)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.report_callback_exception = self.callback_error
        style = ttk.Style(root)
        style.configure('Title.TLabel', font=('Helvetica', 23, 'bold'))
        style.configure('Heading.TLabel', font=('Helvetica', 13, 'bold'))
        style.configure('Status.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Treeview', rowheight=30)
        style.configure('Treeview.Heading', font=('Helvetica', 11, 'bold'))
        outer = ttk.Frame(root, padding=20); outer.pack(fill='both', expand=True)
        header = ttk.Frame(outer); header.pack(fill='x')
        ttk.Label(header, text='STRD', style='Title.TLabel').pack(side='left')
        ttk.Label(header, text='  H-beam strength checker  /  Offline pilot').pack(side='left', padx=12)
        self.sample_button = ttk.Button(header, text='Load demonstration', command=self.load_example)
        self.sample_button.pack(side='right')
        self.reset_button = ttk.Button(header, text='Clear inputs', command=self.reset)
        self.reset_button.pack(side='right', padx=8)
        ttk.Label(outer, text='DPT steel manual | SS400 | Major-axis bending / LTB + web shear | ASD / LRFD').pack(anchor='w', pady=(8,12))
        self.banner = ttk.Label(outer, text='', wraplength=1080)
        self.banner.pack(fill='x', pady=(0,8))
        self.tabs = ttk.Notebook(outer); self.tabs.pack(fill='both', expand=True)
        self.member_tab = ttk.Frame(self.tabs, padding=16)
        self.actions_tab = ttk.Frame(self.tabs, padding=16)
        self.results_tab = ttk.Frame(self.tabs, padding=16)
        for tab, title in [(self.member_tab,'1  Member & applicability'),(self.actions_tab,'2  Segments & load cases'),(self.results_tab,'3  Results & evidence')]: self.tabs.add(tab,text=title)
        self.member_body, self.member_canvas = self.scroll_body(self.member_tab)
        self.actions_body, self.actions_canvas = self.scroll_body(self.actions_tab)
        self.build_member(); self.build_actions(); self.build_results()
        footer = ttk.Frame(outer); footer.pack(side='bottom',fill='x',pady=(14,0),before=self.tabs)
        self.status = ttk.Label(footer, style='Status.TLabel'); self.status.pack(side='left')
        self.calculate_button = ttk.Button(footer, text='Calculate / Recalculate', command=self.calculate)
        self.calculate_button.pack(side='right')
        self.scope_label=ttk.Label(outer, text='Conditional strength checks only. No project saving in P1; closing discards this session.')
        self.scope_label.pack(side='bottom',anchor='w',pady=(8,0),before=footer)
        self.load_forms(); self.refresh_state()

    def scroll_body(self, tab):
        canvas=tk.Canvas(tab,highlightthickness=0)
        scroll=ttk.Scrollbar(tab,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        body=ttk.Frame(canvas)
        window=canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda event:canvas.itemconfigure(window,width=event.width))
        return body,canvas

    def field(self, parent, label, key, path, row, choices=None, boolean=False):
        if boolean:
            var = tk.BooleanVar(parent)
            widget = ttk.Checkbutton(parent, text=label, variable=var)
            widget.grid(row=row, column=0, columnspan=2, sticky='w', pady=3)
        else:
            ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',padx=(0,12),pady=3)
            var = tk.StringVar(parent)
            widget = ttk.Combobox(parent,textvariable=var,values=choices,state='readonly',width=24) if choices else ttk.Entry(parent,textvariable=var,width=24)
            widget.grid(row=row,column=1,sticky='ew',pady=3)
        self.vars[key] = var
        self.widgets[key] = widget
        def changed(*_):
            if self.loading: return
            actual_path = path() if callable(path) else path
            self.session.set_value(actual_path,var.get())
            self.refresh_tables(); self.refresh_state()
        var.trace_add('write',changed)
        parent.columnconfigure(1,weight=1)
        return widget

    def build_member(self):
        box = ttk.LabelFrame(self.member_body,text='Member inputs',padding=14); box.pack(fill='x')
        self.field(box,'Member ID','member_id',('member_id',),0)
        self.field(box,'Section (actual dimensions, mm)','section_id',('section_id',),1,
                   choices=[s['section_id'] for s in self.session.inventory['sections']])
        self.field(box,'Physical member length [mm]','length_mm',('length_mm',),2)
        ttk.Label(box,text='Material: SS400, web/flange <=16 mm | Fy 245 MPa | E 200,000 MPa',wraplength=950).grid(row=3,column=0,columnspan=2,sticky='w',pady=8)
        checks = ttk.LabelFrame(self.member_body,text='Confirm applicability and restraint evidence',padding=14); checks.pack(fill='x',pady=12)
        for i,(key,label) in enumerate(FLAGS.items()):self.field(checks,label,key,('assumptions',key),i,boolean=True)
        ttk.Label(self.member_body,text='These confirmations are your engineering inputs. STRD does not establish the adequacy of bracing or generate loads.\nNot checked: axial/combined actions, minor-axis bending, torsion, deflection, global stability, connections, local bearing, fatigue, seismic or fire.',wraplength=1020,justify='left').pack(anchor='w',pady=6)

    def tree(self,parent,columns,height):
        frame = ttk.Frame(parent); frame.pack(fill='both',expand=True)
        tree = ttk.Treeview(frame,columns=[c[0] for c in columns],show='headings',height=height,selectmode='browse')
        for key,label,width in columns:tree.heading(key,text=label);tree.column(key,width=width,minwidth=50,stretch=True)
        sy=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);sx=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview)
        tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew')
        frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1)
        return tree

    def build_actions(self):
        ttk.Label(self.actions_body,text='Supply maximum absolute M and V for each case/segment; use the selected ASD or LRFD demand basis. No load factors are applied here.',wraplength=1030).pack(anchor='w',pady=(0,10))
        upper=ttk.Frame(self.actions_body);upper.pack(fill='both',expand=True)
        left=ttk.LabelFrame(upper,text='Physical segments',padding=10);left.pack(side='left',fill='both',expand=True,padx=(0,8))
        self.segments_tree=self.tree(left,[('id','ID',55),('start','Start [mm]',85),('end','End [mm]',85),('braced','Continuous',90)],3)
        self.segments_tree.bind('<<TreeviewSelect>>',self.select_segment)
        bar=ttk.Frame(left);bar.pack(fill='x',pady=6)
        ttk.Button(bar,text='+ Segment',command=lambda:self.mutate('add_segment')).pack(side='left')
        ttk.Button(bar,text='Remove selected',command=lambda:self.mutate('remove_segment')).pack(side='left',padx=6)
        form=ttk.Frame(left);form.pack(fill='x')
        self.field(form,'Start [mm]','start_mm',lambda:('segments',self.si,'start_mm'),0)
        self.field(form,'End [mm]','end_mm',lambda:('segments',self.si,'end_mm'),1)
        self.field(form,'Continuously restrained (Lb=0)','continuous_restraint',lambda:('segments',self.si,'continuous_restraint'),2,boolean=True)
        right=ttk.LabelFrame(upper,text='Load cases',padding=10);right.pack(side='left',fill='both',expand=True)
        self.cases_tree=self.tree(right,[('id','Case ID',120),('method','Method',80)],3)
        self.cases_tree.bind('<<TreeviewSelect>>',self.select_case)
        bar=ttk.Frame(right);bar.pack(fill='x',pady=6)
        ttk.Button(bar,text='+ Case',command=lambda:self.mutate('add_case')).pack(side='left')
        ttk.Button(bar,text='Remove selected',command=lambda:self.mutate('remove_case')).pack(side='left',padx=6)
        form=ttk.Frame(right);form.pack(fill='x')
        for row,(key,label,choices) in enumerate([('case_id','Case ID',None),('method','Demand basis',['ASD','LRFD']),('action_source','Action source / reference',None)]):
            self.field(form,label,key,lambda k=key:('cases',self.ci,k),row,choices=choices)
        lower=ttk.LabelFrame(self.actions_body,text='Actions for the selected case and segment',padding=10);lower.pack(fill='x',pady=(12,0))
        self.selected_action=ttk.Label(lower,style='Heading.TLabel');self.selected_action.grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,5))
        for row,(key,label,choices) in enumerate([('moment_knm','Maximum |M| [kN-m]',None),('shear_kn','Maximum |V| [kN]',None),('cb','Cb [1-5]',None),('cb_source','Cb basis',['CONSERVATIVE','VERIFIED_MOMENT_DIAGRAM']),('cb_reference','Cb evidence / reference',None)],1):
            self.field(lower,label,key,lambda k=key:('cases',self.ci,'segments',self.si,k),row,choices=choices)

    def build_results(self):
        self.summary=ttk.Label(self.results_tab,style='Heading.TLabel',wraplength=1020)
        self.summary.pack(anchor='w',pady=(0,10))
        self.result_tree=self.tree(self.results_tab,[('case','Case',95),('segment','Segment',70),('method','Basis',65),('flexure','Flexure',95),('m','M / capacity [kN-m]',185),('mu','M ratio',70),('shear','Shear',95),('v','V / capacity [kN]',175),('vu','V ratio',70)],4)
        self.result_tree.bind('<<TreeviewSelect>>',self.select_result)
        detail_tabs=ttk.Notebook(self.results_tab);detail_tabs.pack(fill='both',expand=True,pady=(10,0))
        self.detail=self.text_panel(detail_tabs,'Selected check details')
        self.trace=self.text_panel(detail_tabs,'Full calculation trace')

    def text_panel(self,parent,title):
        panel=ttk.Frame(parent);parent.add(panel,text=title)
        text=tk.Text(panel,wrap='word',height=12,font=('TkFixedFont',11),padx=12,pady=10,state='disabled')
        scroll=ttk.Scrollbar(panel,command=text.yview);text.configure(yscrollcommand=scroll.set)
        text.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
        return text

    @staticmethod
    def set_text(widget,text):
        widget.configure(state='normal');widget.delete('1.0','end');widget.insert('1.0',text);widget.configure(state='disabled')

    def load_forms(self):
        self.loading=True
        try:
            d=self.session.draft
            for key in ('member_id','section_id','length_mm'):self.vars[key].set(d[key])
            for key in FLAGS:self.vars[key].set(d['assumptions'][key])
            for key in ('start_mm','end_mm','continuous_restraint'):self.vars[key].set(d['segments'][self.si][key])
            for key in ('case_id','method','action_source'):self.vars[key].set(d['cases'][self.ci][key])
            for key in ('moment_knm','shear_kn','cb','cb_source','cb_reference'):self.vars[key].set(d['cases'][self.ci]['segments'][self.si][key])
        finally:self.loading=False
        self.refresh_tables()

    def refresh_tables(self):
        def update(tree,rows,selected):
            wanted={str(i) for i in range(len(rows))}
            for item in tree.get_children():
                if item not in wanted:tree.delete(item)
            for i,values in enumerate(rows):
                if tree.exists(str(i)):tree.item(str(i),values=values)
                else:tree.insert('','end',iid=str(i),values=values)
            if tree.selection()!=(str(selected),):tree.selection_set(str(selected))
        d=self.session.draft
        update(self.segments_tree,[(s['segment_id'],s['start_mm'],s['end_mm'],'Yes' if s['continuous_restraint'] else 'No') for s in d['segments']],self.si)
        update(self.cases_tree,[(c['case_id'],c['method']) for c in d['cases']],self.ci)
        self.selected_action.configure(text=d['cases'][self.ci]['case_id']+' / '+d['segments'][self.si]['segment_id'])

    def select_segment(self,_=None):
        segments=self.segments_tree.selection();cases=self.cases_tree.selection()
        si=int(segments[0]) if segments else self.si
        ci=int(cases[0]) if cases else self.ci
        if (si,ci)!=(self.si,self.ci):
            self.si,self.ci=si,ci
            self.load_forms()

    def select_case(self,_=None):
        self.select_segment()

    def mutate(self,operation):
        try:
            if operation=='remove_segment':self.session.remove_segment(self.si);self.si=max(0,self.si-1)
            elif operation=='remove_case':self.session.remove_case(self.ci);self.ci=max(0,self.ci-1)
            elif operation=='add_segment':self.session.add_segment();self.si=len(self.session.draft['segments'])-1
            else:self.session.add_case();self.ci=len(self.session.draft['cases'])-1
        except DraftError as exc:messagebox.showinfo('Keep one item',str(exc),parent=self.root);return
        self.load_forms();self.refresh_state()

    def refresh_state(self):
        self.banner.configure(text='Demonstration inputs - replace demands and verify all assumptions before using your own result.' if self.session.demonstration else 'One member | In-memory session | Confirm applicability before calculating.')
        if self.session.result is None:
            label='Not calculated' if self.session.state=='EMPTY' else 'Inputs changed - recalculate'
            self.status.configure(text=label,foreground='#8a4b00')
            self.summary.configure(text=label)
            self.result_tree.delete(*self.result_tree.get_children())
            self.set_text(self.detail,'No current result. Complete inputs and select Calculate / Recalculate.')
            self.set_text(self.trace,'No current calculation trace.')

    def calculate(self):
        try:result=self.session.calculate()
        except Exception as exc:
            self.session.invalidate();self.refresh_state();self.status.configure(text='Calculation error - no current result',foreground='#a01d25')
            self.summary.configure(text='Calculation error: '+str(exc));self.tabs.select(self.results_tab);return
        self.tabs.select(self.results_tab)
        status=result['status']
        labels={'CHECKS_PASS':'Checks pass - conditional strength only','CHECKS_FAIL':'Strength check failed','INCOMPLETE':'Incomplete - some checks not performed','INVALID_INPUT':'Invalid input','UNSUPPORTED':'Outside supported scope'}
        self.status.configure(text=labels.get(status,status),foreground='#216142' if status=='CHECKS_PASS' else '#a01d25')
        coverage=result.get('coverage',{})
        self.summary.configure(text=labels.get(status,status)+'\n'+result['message']+f"  Completed {coverage.get('completed',0)} / {coverage.get('expected','-')} checks.")
        self.result_tree.delete(*self.result_tree.get_children())
        for i,rec in enumerate(result.get('records',[])):
            f,s=rec['flexure'],rec['shear']
            def pair(c,field,cap):return f"{c['inputs'][field]:.8g} / {c[cap]:.8g}" if cap in c else 'Not calculated'
            def ratio(c):return format(c['utilization'],'.8g') if 'utilization' in c else '-'
            self.result_tree.insert('','end',iid=str(i),values=(rec['case_id'],rec['segment']['segment_id'],rec['method'],f['status'],pair(f,'moment_knm','capacity_knm'),ratio(f),s['status'],pair(s,'shear_kn','capacity_kn'),ratio(s)))
        self.set_text(self.trace,json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
        if self.result_tree.get_children():self.result_tree.selection_set('0');self.select_result()
        else:self.set_text(self.detail,result['message']+'\n\nUnperformed checks:\n'+'\n'.join(result.get('not_checked',[])))

    def select_result(self,_=None):
        selected=self.result_tree.selection();result=self.session.result
        if not selected or result is None:return
        rec=result['records'][int(selected[0])]
        lines=[rec['case_id']+' / '+rec['segment']['segment_id']+' | '+rec['method'],
               'Action source: '+rec['action_source'],'Physical segment: '+str(rec['segment']['start_mm'])+' to '+str(rec['segment']['end_mm'])+' mm; continuous restraint: '+str(rec['segment']['continuous_restraint']), '']
        for kind in ('flexure','shear'):
            c=rec[kind];lines.extend([kind.upper()+' - '+c['status'],c['message']])
            for key in ('capacity_knm','capacity_kn','utilization','governing_limit_state'):
                if key in c:
                    label={'capacity_knm':'Flexural capacity [kN-m]','capacity_kn':'Shear capacity [kN]','utilization':'Demand / capacity','governing_limit_state':'Governing limit state'}[key]
                    lines.append(label+': '+str(c[key]))
            lines.append('Intermediate values:')
            lines.extend('  '+k+': '+str(v) for k,v in c.get('intermediates',{}).items())
            if 'reference' in c:lines.append('References: '+', '.join(c['reference']['clauses']))
            lines.extend(c.get('warnings',[]));lines.append('')
        lines+=['NOT CHECKED']+result['not_checked']
        lines+=['','Catalog: '+result['data_snapshot']['catalog_revision'],'Snapshot: '+result['snapshot_sha256'],
                'Full source hashes, inputs and assumptions are in Full calculation trace.']
        self.set_text(self.detail,'\n'.join(lines))

    def load_example(self):
        if not messagebox.askyesno('Replace this session?', 'Load demonstration inputs? Current in-memory inputs will be replaced.',parent=self.root):return
        self.session.load_example();self.ci=self.si=0;self.load_forms();self.refresh_state();self.tabs.select(self.member_tab)

    def reset(self):
        if not messagebox.askyesno('Clear this session?', 'Discard all inputs and results? P1 has no Save/Open.',parent=self.root):return
        self.session=MemberSession();self.ci=self.si=0;self.load_forms();self.refresh_state();self.tabs.select(self.member_tab)

    def close(self):
        if messagebox.askyesno('Close STRD?', 'Close and discard this in-memory session? P1 has no Save/Open.',parent=self.root):self.root.destroy()

    def callback_error(self,kind,error,traceback):
        self.session.invalidate();self.refresh_state()
        self.status.configure(text='Application error - no current result',foreground='#a01d25')
        messagebox.showerror('STRD application error',str(error),parent=self.root)
