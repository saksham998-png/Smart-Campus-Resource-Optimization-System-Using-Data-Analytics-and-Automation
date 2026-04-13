from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from datetime import datetime
import io
import tempfile
import os


def create_header_footer(canvas_obj, doc):
    """Add header and footer to each page"""
    canvas_obj.saveState()
    
    # Header
    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.setFillColor(colors.HexColor('#1a8060'))
    canvas_obj.drawString(0.75*inch, doc.height + 1.5*inch, "Smart Campus Analytics Report")
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#4a8070'))
    canvas_obj.drawString(0.75*inch, doc.height + 1.3*inch, f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    
    # Footer
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#4a8070'))
    page_num = canvas_obj.getPageNumber()
    text = f"Page {page_num}"
    canvas_obj.drawRightString(doc.width + 0.75*inch, 0.5*inch, text)
    
    canvas_obj.restoreState()


def generate_analysis_report(date_from, date_to, block, data):
    """
    Generate a comprehensive PDF report
    
    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        block: Selected block ('ALL', 'A', 'B', 'C', or 'D')
        data: Analysis data dictionary containing matches and block_summary
    
    Returns:
        BytesIO object containing the PDF
    """
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1.8*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0f2d25'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#4a8070'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a8060'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#2d3acc'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#0f2d25'),
        spaceAfter=8,
        leading=14,
        fontName='Helvetica'
    )
    
    # ═══════════════════════════════════════════════════════════
    # TITLE PAGE
    # ═══════════════════════════════════════════════════════════
    
    story.append(Spacer(1, 1.5*inch))
    
    title = Paragraph("📊 Smart Campus Analytics Report", title_style)
    story.append(title)
    
    subtitle = Paragraph(f"Planned vs Live Analysis<br/>{date_from} to {date_to}", subtitle_style)
    story.append(subtitle)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Report metadata box
    metadata_data = [
        ['Report Period:', f'{date_from} to {date_to}'],
        ['Block Filter:', block if block != 'ALL' else 'All Blocks'],
        ['Total Entries:', str(len(data['matches']))],
        ['Generated On:', datetime.now().strftime('%B %d, %Y at %I:%M %p')]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[2*inch, 3.5*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f5f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0f2d25')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c8e8de')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(metadata_table)
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════
    # EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════
    
    story.append(Paragraph("Executive Summary", heading_style))
    
    # Filter matches based on block
    matches = data['matches'] if block == 'ALL' else [m for m in data['matches'] if m['building'] == block]
    
    if not matches:
        story.append(Paragraph(
            f"<b>No matched entries found</b> for the selected criteria. "
            f"A match requires both a planned entry and a live entry for the same block, date, and time slot.",
            body_style
        ))
        doc.build(story, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
        buffer.seek(0)
        return buffer
    
    # Calculate aggregates
    total_planned_elec = sum(m['planned_elec'] for m in matches)
    total_live_elec = sum(m['live_elec'] for m in matches)
    total_planned_water = sum(m['planned_water'] for m in matches)
    total_live_water = sum(m['live_water'] for m in matches)
    total_planned_rooms = sum(m['planned_rooms'] for m in matches)
    total_live_rooms = sum(m['live_rooms'] for m in matches)
    
    def calc_diff_pct(planned, live):
        return round(((live - planned) / planned * 100), 1) if planned > 0 else 0
    
    elec_diff_pct = calc_diff_pct(total_planned_elec, total_live_elec)
    water_diff_pct = calc_diff_pct(total_planned_water, total_live_water)
    rooms_diff_pct = calc_diff_pct(total_planned_rooms, total_live_rooms)
    
    # Summary paragraph
    summary_text = f"""
    This report analyzes <b>{len(matches)} matched entries</b> where both planned and live data exist 
    for the same block, date, and time slot. The analysis covers the period from <b>{date_from}</b> to <b>{date_to}</b> 
    {f'for <b>Block {block}</b>' if block != 'ALL' else 'across <b>all blocks</b>'}.
    <br/><br/>
    <b>Key Findings:</b><br/>
    • Electricity usage was <b>{abs(elec_diff_pct)}% {'higher' if elec_diff_pct > 0 else 'lower'}</b> than planned 
    ({int(total_live_elec)} units vs {int(total_planned_elec)} units planned)<br/>
    • Water consumption was <b>{abs(water_diff_pct)}% {'higher' if water_diff_pct > 0 else 'lower'}</b> than planned 
    ({int(total_live_water)}L vs {int(total_planned_water)}L planned)<br/>
    • Room utilization was <b>{abs(rooms_diff_pct)}% {'higher' if rooms_diff_pct > 0 else 'lower'}</b> than planned 
    ({total_live_rooms} rooms vs {total_planned_rooms} rooms planned)
    """
    
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Summary statistics table
    summary_data = [
        ['Metric', 'Planned', 'Actual (Live)', 'Deviation', 'Status'],
        ['⚡ Electricity (units)', f'{int(total_planned_elec):,}', f'{int(total_live_elec):,}', 
         f'{elec_diff_pct:+.1f}%', get_status_text(elec_diff_pct)],
        ['💧 Water (liters)', f'{int(total_planned_water):,}', f'{int(total_live_water):,}', 
         f'{water_diff_pct:+.1f}%', get_status_text(water_diff_pct)],
        ['🏫 Rooms Used', f'{total_planned_rooms}', f'{total_live_rooms}', 
         f'{rooms_diff_pct:+.1f}%', get_status_text(rooms_diff_pct)],
    ]
    
    summary_table = Table(summary_data, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1*inch, 1.1*inch])
    summary_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a8060')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0f2d25')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        
        # Borders and padding
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c8e8de')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fcfb')]),
    ]))
    
    story.append(summary_table)
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════
    # BLOCK-BY-BLOCK ANALYSIS
    # ═══════════════════════════════════════════════════════════
    
    if block == 'ALL':
        story.append(Paragraph("Block-by-Block Analysis", heading_style))
        
        block_summary = data['block_summary']
        active_blocks = [b for b in ['A', 'B', 'C', 'D'] if block_summary.get(b, {}).get('count', 0) > 0]
        
        for blk in active_blocks:
            bs = block_summary[blk]
            
            story.append(Paragraph(f"🏛️ Block {blk}", subheading_style))
            
            block_text = f"""
            Block {blk} had <b>{bs['count']} matched entries</b> during the analysis period.
            <br/><br/>
            <b>Performance Overview:</b><br/>
            • Average electricity deviation: <b>{bs['avg_elec_diff']:+.1f}%</b> ({int(bs['total_live_elec'])} units actual vs {int(bs['total_planned_elec'])} planned)<br/>
            • Average water deviation: <b>{bs['avg_water_diff']:+.1f}%</b> ({int(bs['total_live_water'])}L actual vs {int(bs['total_planned_water'])}L planned)<br/>
            • Average room utilization deviation: <b>{bs['avg_rooms_diff']:+.1f}%</b> ({bs['total_live_rooms']} rooms actual vs {bs['total_planned_rooms']} planned)
            """
            
            story.append(Paragraph(block_text, body_style))
            
            # Insights for this block
            insights = []
            if abs(bs['avg_elec_diff']) > 15:
                insights.append(f"⚠️ Significant electricity {'overuse' if bs['avg_elec_diff'] > 0 else 'underuse'} detected")
            if abs(bs['avg_water_diff']) > 15:
                insights.append(f"💧 Water consumption {'exceeded' if bs['avg_water_diff'] > 0 else 'below'} expectations")
            if abs(bs['avg_rooms_diff']) > 20:
                insights.append(f"🏫 Room utilization was {'higher' if bs['avg_rooms_diff'] > 0 else 'lower'} than planned")
            
            if insights:
                story.append(Paragraph("<b>Action Items:</b>", body_style))
                for insight in insights:
                    story.append(Paragraph(f"• {insight}", body_style))
            
            story.append(Spacer(1, 0.15*inch))
        
        story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════
    # DETAILED ENTRY ANALYSIS
    # ═══════════════════════════════════════════════════════════
    
    story.append(Paragraph("Detailed Entry Analysis", heading_style))
    
    story.append(Paragraph(
        f"The following table shows all {len(matches)} matched entries with detailed comparisons between "
        f"planned allocations and actual (live) usage. Entries are sorted by date and time slot.",
        body_style
    ))
    
    story.append(Spacer(1, 0.1*inch))
    
    # Sort matches by date
    sorted_matches = sorted(matches, key=lambda x: (x['date'], x.get('slot', '')))
    
    # Split into chunks for multiple pages if needed
    chunk_size = 20
    for chunk_idx in range(0, len(sorted_matches), chunk_size):
        chunk = sorted_matches[chunk_idx:chunk_idx + chunk_size]
        
        # Detailed table
        detail_headers = ['Date', 'Slot', 'Block', 'Rooms\nP/L', 'Elec (units)\nP/L', 'Water (L)\nP/L', 'Status']
        detail_data = [detail_headers]
        
        for m in chunk:
            slot_text = m.get('slot', '—')
            if slot_text == 'nan':
                slot_text = '—'
            
            rooms_text = f"{m['planned_rooms']}/{m['live_rooms']}"
            elec_text = f"{int(m['planned_elec'])}/{int(m['live_elec'])}"
            water_text = f"{int(m['planned_water'])}/{int(m['live_water'])}"
            
            # Determine overall status
            max_dev = max(abs(m['elec_diff_pct']), abs(m['water_diff_pct']), abs(m['rooms_diff_pct']))
            if max_dev > 30:
                status = '🔴 High'
            elif max_dev > 10:
                status = '🟡 Medium'
            else:
                status = '🟢 OK'
            
            detail_data.append([
                m['date'],
                slot_text[:10] if len(slot_text) > 10 else slot_text,
                m['building'],
                rooms_text,
                elec_text,
                water_text,
                status
            ])
        
        detail_table = Table(detail_data, colWidths=[1*inch, 1*inch, 0.6*inch, 0.8*inch, 1.1*inch, 1*inch, 0.8*inch])
        detail_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3acc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c8e8de')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            
            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafcfb')]),
        ]))
        
        story.append(detail_table)
        
        if chunk_idx + chunk_size < len(sorted_matches):
            story.append(Spacer(1, 0.15*inch))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════
    
    story.append(Paragraph("Recommendations & Action Items", heading_style))
    
    recommendations = []
    
    # Electricity recommendations
    if elec_diff_pct > 15:
        recommendations.append({
            'icon': '⚡',
            'title': 'High Electricity Consumption',
            'desc': f'Actual electricity usage exceeded planned by {elec_diff_pct:.1f}%. Consider conducting an energy audit and implementing power-saving measures.',
            'actions': [
                'Install motion-sensor lights in low-traffic areas',
                'Switch to LED lighting in high-usage buildings',
                'Review HVAC schedules and optimize temperature settings',
                'Educate staff on energy conservation practices'
            ]
        })
    elif elec_diff_pct < -15:
        recommendations.append({
            'icon': '💡',
            'title': 'Lower Than Expected Electricity Use',
            'desc': f'Actual electricity usage was {abs(elec_diff_pct):.1f}% below planned. This may indicate underutilization of facilities.',
            'actions': [
                'Review room booking efficiency',
                'Consider consolidating classes to reduce active buildings',
                'Update baseline electricity estimates for future planning'
            ]
        })
    
    # Water recommendations
    if water_diff_pct > 15:
        recommendations.append({
            'icon': '💧',
            'title': 'High Water Consumption',
            'desc': f'Actual water usage exceeded planned by {water_diff_pct:.1f}%. Investigate potential leaks or inefficiencies.',
            'actions': [
                'Conduct leak detection survey across all buildings',
                'Install water-efficient fixtures in restrooms',
                'Monitor water meters more frequently',
                'Implement rainwater harvesting for landscaping'
            ]
        })
    
    # Room utilization recommendations
    if abs(rooms_diff_pct) > 20:
        recommendations.append({
            'icon': '🏫',
            'title': 'Room Utilization Mismatch',
            'desc': f'Room usage was {abs(rooms_diff_pct):.1f}% {"higher" if rooms_diff_pct > 0 else "lower"} than planned.',
            'actions': [
                'Improve coordination between timetabling and facility planning',
                'Implement real-time room booking system',
                'Review class size distributions and room assignments',
                'Consider flexible classroom configurations'
            ]
        })
    
    # General best practices
    recommendations.append({
        'icon': '📊',
        'title': 'Data Collection & Monitoring',
        'desc': 'Continue tracking planned vs live data to improve prediction accuracy.',
        'actions': [
            'Ensure consistent data entry for all time slots',
            'Train staff on the importance of accurate live data reporting',
            'Review and update baseline metrics quarterly',
            'Set up automated alerts for significant deviations'
        ]
    })
    
    for rec in recommendations:
        story.append(Paragraph(f"{rec['icon']} {rec['title']}", subheading_style))
        story.append(Paragraph(rec['desc'], body_style))
        story.append(Paragraph("<b>Recommended Actions:</b>", body_style))
        for action in rec['actions']:
            story.append(Paragraph(f"  • {action}", body_style))
        story.append(Spacer(1, 0.15*inch))
    
    # ═══════════════════════════════════════════════════════════
    # APPENDIX - METHODOLOGY
    # ═══════════════════════════════════════════════════════════
    
    story.append(PageBreak())
    story.append(Paragraph("Appendix: Methodology", heading_style))
    
    methodology_text = """
    <b>Data Matching:</b><br/>
    Entries are considered "matched" when both a planned entry and a live entry exist for the same 
    building, date, and time slot. Only matched entries are included in this analysis.
    <br/><br/>
    <b>Deviation Calculation:</b><br/>
    Deviation percentages are calculated as: ((Actual - Planned) / Planned) × 100
    <br/><br/>
    <b>Status Classification:</b><br/>
    • <b>OK (🟢):</b> Deviation ≤ 10% from planned<br/>
    • <b>Medium (🟡):</b> Deviation between 10% and 30%<br/>
    • <b>High (🔴):</b> Deviation > 30% from planned
    <br/><br/>
    <b>Baseline Metrics:</b><br/>
    Planned values are calculated using per-room baseline metrics derived from historical data, 
    multiplied by the number of planned rooms for each time slot.
    <br/><br/>
    <b>Data Sources:</b><br/>
    All data is sourced from the Smart Campus Management System, combining automated sensor readings 
    (live data) with manual timetable entries (planned data).
    """
    
    story.append(Paragraph(methodology_text, body_style))
    
    # Build PDF
    doc.build(story, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
    
    buffer.seek(0)
    return buffer


def get_status_text(deviation_pct):
    """Convert deviation percentage to status text"""
    abs_dev = abs(deviation_pct)
    if abs_dev <= 10:
        return '🟢 On Target'
    elif abs_dev <= 30:
        return '🟡 Moderate'
    else:
        return '🔴 Significant'