import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

def get_image_base64():
    """
    Saves current matplotlib figure to buffer and converts it to a base64 encoded string.
    """
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100, facecolor='#111827')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_str

def generate_status_pie_chart(placed_count, intern_count, both_count, unplaced_count):
    labels = ['Placed', 'Internship', 'Placed & Intern', 'Unplaced']
    sizes = [placed_count, intern_count, both_count, unplaced_count]
    
    # Filter out zero sizes to avoid empty wedges in pie chart
    filtered = [(l, s) for l, s in zip(labels, sizes) if s > 0]
    if not filtered:
        return ""
    labels, sizes = zip(*filtered)
    
    colors = ['#10b981', '#3b82f6', '#6366f1', '#ef4444']
    
    fig, ax = plt.subplots(figsize=(5, 4))
    
    plt.rcParams['text.color'] = '#9ca3af'
    plt.rcParams['axes.labelcolor'] = '#9ca3af'
    
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=140, 
        colors=colors[:len(sizes)],
        textprops=dict(color="#d1d5db", weight="bold")
    )
    ax.axis('equal')
    
    return get_image_base64()

def generate_dept_bar_chart(dept_names, avg_packages, placement_ratios):
    if not dept_names:
        return ""
        
    fig, ax1 = plt.subplots(figsize=(6, 4))
    
    plt.rcParams['text.color'] = '#9ca3af'
    
    color = '#3b82f6'
    ax1.set_xlabel('Departments', color='#9ca3af')
    ax1.set_ylabel('Average Package (LPA)', color=color)
    bars1 = ax1.bar(dept_names, avg_packages, color=color, alpha=0.7, width=0.4, align='center')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.tick_params(axis='x', labelcolor='#9ca3af')
    ax1.set_facecolor('#1f2937')
    ax1.spines['bottom'].set_color('#374151')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#374151')
    
    ax2 = ax1.twinx()  
    color = '#10b981'
    ax2.set_ylabel('Placement Ratio (%)', color=color)
    
    import numpy as np
    x = np.arange(len(dept_names))
    bars2 = ax2.bar(x + 0.2, placement_ratios, color=color, alpha=0.7, width=0.4, align='center')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['right'].set_color('#374151')
    
    return get_image_base64()

def generate_batch_line_chart(batch_names, placement_ratios):
    if not batch_names:
        return ""
        
    fig, ax = plt.subplots(figsize=(6, 4))
    
    ax.plot(batch_names, placement_ratios, marker='o', color='#6366f1', linewidth=2.5, markersize=8)
    ax.set_ylabel('Placement Ratio (%)', color='#9ca3af')
    ax.set_xlabel('Batches', color='#9ca3af')
    ax.tick_params(axis='both', labelcolor='#9ca3af')
    ax.set_facecolor('#1f2937')
    ax.spines['bottom'].set_color('#374151')
    ax.spines['left'].set_color('#374151')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, color='#374151', linestyle='--', alpha=0.5)
    
    return get_image_base64()

def generate_student_scatter_plot(cgpas, packages):
    if not cgpas:
        return ""
        
    fig, ax = plt.subplots(figsize=(6, 4))
    
    ax.scatter(cgpas, packages, color='#f59e0b', alpha=0.8, edgecolors='none', s=60)
    ax.set_xlabel('Student CGPA', color='#9ca3af')
    ax.set_ylabel('CTC Package Offered (LPA)', color='#9ca3af')
    ax.tick_params(axis='both', labelcolor='#9ca3af')
    ax.set_facecolor('#1f2937')
    ax.spines['bottom'].set_color('#374151')
    ax.spines['left'].set_color('#374151')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, color='#374151', linestyle='--', alpha=0.5)
    
    return get_image_base64()

def generate_company_bar_chart(company_names, hires_counts):
    if not company_names:
        return ""
        
    fig, ax = plt.subplots(figsize=(6, 4))
    
    ax.barh(company_names, hires_counts, color='#a5b4fc', alpha=0.8)
    ax.set_xlabel('Selections Hires Count', color='#9ca3af')
    ax.set_ylabel('Companies', color='#9ca3af')
    ax.tick_params(axis='both', labelcolor='#9ca3af')
    ax.set_facecolor('#1f2937')
    ax.spines['bottom'].set_color('#374151')
    ax.spines['left'].set_color('#374151')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    return get_image_base64()
