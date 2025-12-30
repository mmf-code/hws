#!/usr/bin/env python3
"""
PDF Generation Script using ReportLab
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def create_report():
    output_path = '/home/user/hws/project/VERIFICATION_REPORT.pdf'
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    heading1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.darkblue,
        spaceBefore=20,
        spaceAfter=10
    )

    heading2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=9,
        backColor=colors.lightgrey,
        leftIndent=10,
        spaceAfter=8
    )

    status_ok = ParagraphStyle(
        'StatusOK',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.green,
        fontName='Helvetica-Bold'
    )

    status_alt = ParagraphStyle(
        'StatusAlt',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.orange,
        fontName='Helvetica-Bold'
    )

    elements = []

    # Title Page
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph('Team 14', title_style))
    elements.append(Paragraph('Proje Dogrulama Raporu', title_style))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph('KON414E - Principles of Robot Autonomy', styles['Heading2']))
    elements.append(Paragraph('3D SLAM and Autonomous Navigation', styles['Heading2']))
    elements.append(Spacer(1, 1*cm))

    info_data = [
        ['Takim Uyeleri:', 'Ceylan Tolunay, Atakan Yaman, Eren Yucetürk'],
        ['Robot:', 'Pioneer 3-DX (Differential Drive)'],
        ['Ortam:', 'Clearpath Robotics Office World'],
        ['Tarih:', 'Aralik 2024'],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)

    elements.append(PageBreak())

    # Section 1: Giris
    elements.append(Paragraph('1. Giris', heading1_style))
    elements.append(Paragraph(
        'Bu rapor, Team 14 projesinin PDF gereksinimlerine uygunlugunu dogrulamak '
        'amaciyla hazirlanmistir. Her adim icin PDF\'te istenen gereksinim, '
        'FINAL_REPORT.md\'de yazilan aciklama ve kod dosyalarindaki gercek '
        'implementasyon karsilastirilmis ve dogrulanmistir.',
        body_style
    ))

    # Section 2: Adim Adim Dogrulama
    elements.append(Paragraph('2. Adim Adim Dogrulama', heading1_style))

    # Step 1
    elements.append(Paragraph('2.1 Step 1: EKF Sensor Fusion (IMU + Wheel Odometry)', heading2_style))
    elements.append(Paragraph('<b>PDF Gereksinimi:</b>', body_style))
    elements.append(Paragraph('"Use robot_localization package to fuse IMU and wheel odometry data."', code_style))

    elements.append(Paragraph('<b>Kod Dogrulamasi:</b>', body_style))
    step1_data = [
        ['Dosya', 'Satir', 'Icerik'],
        ['robot_localization.yaml', '31-36', 'odom0: /odom tanimli'],
        ['robot_localization.yaml', '43-52', 'imu0: /imu/data tanimli'],
        ['p3dx_hw2.urdf.xacro', '456-473', 'IMU sensor plugin'],
        ['slam_hybrid.launch.py', '156-166', 'EKF node baslatma'],
    ]
    step1_table = Table(step1_data, colWidths=[5*cm, 2*cm, 7*cm])
    step1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(step1_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph('Dogrulama Sonucu: TAMAMEN UYGUN', status_ok))

    # Step 2
    elements.append(Paragraph('2.2 Step 2: Depth to PointCloud2 Conversion', heading2_style))
    elements.append(Paragraph('<b>PDF Gereksinimi:</b>', body_style))
    elements.append(Paragraph('"Convert (if needed) the depth data of the RGBD camera to PointCloud2 message."', code_style))

    elements.append(Paragraph('<b>Kod Dogrulamasi:</b>', body_style))
    step2_data = [
        ['Dosya', 'Satir', 'Icerik'],
        ['p3dx_hw2.urdf.xacro', '420-451', 'RGBD camera sensor tanimi'],
        ['p3dx_hw2.urdf.xacro', '442', 'points:=depth/points remapping'],
    ]
    step2_table = Table(step2_data, colWidths=[5*cm, 2*cm, 7*cm])
    step2_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(step2_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph('Dogrulama Sonucu: TAMAMEN UYGUN', status_ok))

    elements.append(PageBreak())

    # Step 3
    elements.append(Paragraph('2.3 Step 3: 3D SLAM - Visual Mode (faster_lio or similar)', heading2_style))
    elements.append(Paragraph('<b>PDF Gereksinimi:</b>', body_style))
    elements.append(Paragraph('"Use faster_lio SLAM package or similar for 3D map building"', code_style))

    elements.append(Paragraph('<b>Kod Dogrulamasi:</b>', body_style))
    step3_data = [
        ['Dosya', 'Satir', 'Icerik'],
        ['rtabmap_rgbd.yaml', '49-51', 'Kp/DetectorStrategy: 6 (GFTT)'],
        ['rtabmap_rgbd.yaml', '55-60', 'Loop closure parametreleri'],
        ['slam_hybrid.launch.py', '196-267', 'RTAB-Map node konfigurasyonu'],
    ]
    step3_table = Table(step3_data, colWidths=[5*cm, 2*cm, 7*cm])
    step3_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(step3_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph('Dogrulama Sonucu: ALTERNATIF COZUM - KABUL EDILEBILIR', status_alt))
    elements.append(Paragraph(
        '<b>Aciklama:</b> PDF\'te "or similar" ifadesi bulunmaktadir. RTAB-Map Visual SLAM, '
        'faster_lio\'nun islevsel karsiligi olarak kullanilmistir.',
        body_style
    ))

    # Step 4
    elements.append(Paragraph('2.4 Step 4: 3D SLAM - ICP Mode (fast_lio or similar)', heading2_style))
    elements.append(Paragraph('<b>PDF Gereksinimi:</b>', body_style))
    elements.append(Paragraph('"Use fast_lio SLAM package or similar for 3D map building"', code_style))

    elements.append(Paragraph('<b>Kod Dogrulamasi:</b>', body_style))
    step4_data = [
        ['Dosya', 'Satir', 'Icerik'],
        ['rtabmap_icp.yaml', '38', 'Reg/Strategy: 1 (ICP registration)'],
        ['rtabmap_icp.yaml', '42-54', 'ICP parametreleri'],
        ['rtabmap_icp.yaml', '68-71', 'g2o optimizer, 100 iterasyon'],
    ]
    step4_table = Table(step4_data, colWidths=[5*cm, 2*cm, 7*cm])
    step4_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(step4_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph('Dogrulama Sonucu: ALTERNATIF COZUM - KABUL EDILEBILIR', status_alt))

    elements.append(PageBreak())

    # Step 5
    elements.append(Paragraph('2.5 Step 5: Localization Performance Comparison', heading2_style))
    elements.append(Paragraph('<b>PDF Gereksinimi:</b>', body_style))
    elements.append(Paragraph('"Compare localization performance with ground truth achieved by gazebo plugin"', code_style))

    elements.append(Paragraph('<b>Kod Dogrulamasi:</b>', body_style))
    step5_data = [
        ['Dosya', 'Satir', 'Icerik'],
        ['p3dx_hw2.urdf.xacro', '487-500', 'Ground truth plugin (libgazebo_ros_p3d.so)'],
        ['evaluation_node.py', '66-72', '/ground_truth/odom subscription'],
        ['evaluation_node.py', '158-207', 'RMSE, ATE, RPE fonksiyonlari'],
    ]
    step5_table = Table(step5_data, colWidths=[5*cm, 2*cm, 7*cm])
    step5_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(step5_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph('Dogrulama Sonucu: TAMAMEN UYGUN', status_ok))

    # Step 6
    elements.append(Paragraph('2.6 Step 6: 3D Mapping Performance Comparison', heading2_style))
    elements.append(Paragraph('<b>PDF Gereksinimi:</b>', body_style))
    elements.append(Paragraph('"Compare 3D mapping performance qualitatively and quantitively (e.g. point cloud density)"', code_style))

    elements.append(Paragraph('<b>Kod Dogrulamasi:</b>', body_style))
    step6_data = [
        ['Dosya', 'Satir', 'Icerik'],
        ['map_metrics.py', '130-142', 'calculate_density_3d()'],
        ['map_metrics.py', '144-153', 'calculate_density_2d()'],
        ['map_metrics.py', '155-163', 'calculate_coverage_2d()'],
        ['map_metrics.py', '165-173', 'calculate_volume()'],
    ]
    step6_table = Table(step6_data, colWidths=[5*cm, 2*cm, 7*cm])
    step6_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(step6_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph('Dogrulama Sonucu: TAMAMEN UYGUN', status_ok))

    # Step 7
    elements.append(Paragraph('2.7 Step 7: 2D Projection + Autonomous Navigation', heading2_style))
    elements.append(Paragraph('<b>PDF Gereksinimi:</b>', body_style))
    elements.append(Paragraph('"Use 2D projection of 3D map for navigation with nav2 packages"', code_style))

    elements.append(Paragraph('<b>Kod Dogrulamasi:</b>', body_style))
    step7_data = [
        ['Dosya', 'Satir', 'Icerik'],
        ['slam_hybrid.launch.py', '238', 'RGBD/CreateOccupancyGrid: true'],
        ['nav2_params.yaml', '105-167', 'Controller server (DWB)'],
        ['nav2_params.yaml', '241-250', 'Planner server (NavFn)'],
    ]
    step7_table = Table(step7_data, colWidths=[5*cm, 2*cm, 7*cm])
    step7_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(step7_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph('Dogrulama Sonucu: TAMAMEN UYGUN', status_ok))

    elements.append(PageBreak())

    # Section 3: Sonuc Tablosu
    elements.append(Paragraph('3. Sonuc Tablosu', heading1_style))

    summary_data = [
        ['Adim', 'PDF Gereksinimi', 'Implementasyon', 'Durum'],
        ['1', 'EKF Sensor Fusion', 'robot_localization', 'TAMAMEN UYGUN'],
        ['2', 'Depth to PointCloud2', 'Gazebo RGBD Plugin', 'TAMAMEN UYGUN'],
        ['3', 'faster_lio or similar', 'RTAB-Map Visual', 'ALTERNATIF'],
        ['4', 'fast_lio or similar', 'RTAB-Map ICP', 'ALTERNATIF'],
        ['5', 'Localization Comparison', 'evaluation_node.py', 'TAMAMEN UYGUN'],
        ['6', 'Mapping Comparison', 'map_metrics.py', 'TAMAMEN UYGUN'],
        ['7', 'Nav2 Navigation', 'Nav2 + RTAB-Map Grid', 'TAMAMEN UYGUN'],
    ]
    summary_table = Table(summary_data, colWidths=[1.5*cm, 4.5*cm, 4.5*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        # Green for TAMAMEN UYGUN rows
        ('TEXTCOLOR', (3, 1), (3, 2), colors.green),
        ('TEXTCOLOR', (3, 5), (3, 7), colors.green),
        # Orange for ALTERNATIF rows
        ('TEXTCOLOR', (3, 3), (3, 4), colors.orange),
    ]))
    elements.append(summary_table)

    # Section 4: Genel Degerlendirme
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph('4. Genel Degerlendirme', heading1_style))

    elements.append(Paragraph('4.1 Uyumluluk Ozeti', heading2_style))
    elements.append(Paragraph('- 5/7 adim: Tam uyumlu (Step 1, 2, 5, 6, 7)', body_style))
    elements.append(Paragraph('- 2/7 adim: Alternatif cozum (Step 3, 4) - PDF\'te "or similar" ifadesi mevcut', body_style))

    elements.append(Paragraph('4.2 Alternatif Cozum Gerekceleri', heading2_style))
    elements.append(Paragraph(
        'Step 3 ve Step 4 icin faster_lio/fast_lio yerine RTAB-Map kullanilmasinin nedenleri:',
        body_style
    ))
    elements.append(Paragraph('1. RTAB-Map ROS 2 Humble ile native uyumlu', body_style))
    elements.append(Paragraph('2. Ayni paket icinde hem Visual hem ICP mode destegi', body_style))
    elements.append(Paragraph('3. Entegre 2D occupancy grid uretimi (Nav2 icin)', body_style))
    elements.append(Paragraph('4. RGBD kamera ile dogrudan calisabilme', body_style))

    elements.append(Paragraph('4.3 Sonuc', heading2_style))
    elements.append(Paragraph(
        'Rapordaki tum ifadeler kodlarla dogrulanmistir. Halusinasyon veya yanlis '
        'bilgi tespit edilmemistir. Proje gereksinimleri basariyla karsilanmistir.',
        body_style
    ))

    # Section 5: Dosya Konumlari
    elements.append(PageBreak())
    elements.append(Paragraph('5. Dosya Konum Tablosu', heading1_style))

    files_data = [
        ['Gereksinim', 'Dosya Adi', 'Dizin'],
        ['EKF Config', 'robot_localization.yaml', 'src/robot_project/config/'],
        ['RTAB-Map Visual', 'rtabmap_rgbd.yaml', 'src/robot_project/config/'],
        ['RTAB-Map ICP', 'rtabmap_icp.yaml', 'src/robot_project/config/'],
        ['Nav2 Config', 'nav2_params.yaml', 'src/robot_project/config/'],
        ['Robot URDF', 'p3dx_hw2.urdf.xacro', 'src/robot_hw1/urdf/'],
        ['Evaluation Node', 'evaluation_node.py', 'src/robot_project/robot_project/'],
        ['Map Metrics', 'map_metrics.py', 'src/robot_project/robot_project/'],
        ['Main Launch', 'slam_hybrid.launch.py', 'src/robot_project/launch/'],
    ]
    files_table = Table(files_data, colWidths=[4*cm, 5*cm, 6*cm])
    files_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(files_table)

    # Build PDF
    doc.build(elements)
    print(f'PDF created successfully: {output_path}')
    return output_path

if __name__ == '__main__':
    create_report()
