"""
RedCube AI 专业级HTML模板系统
Professional HTML Template System for RedCube AI Workflow

基于您展示的RedCube AI设计风格，创建专业级的HTML模板系统
包含4种核心模板：封面页、内容页、对比页、结尾页
"""

class RedCubeTemplateSystem:
    """RedCube AI专业级模板系统"""
    
    def __init__(self):
        self.base_style = self._get_base_style()
        self.color_scheme = {
            "primary_blue": "#2563eb",
            "success_green": "#10b981", 
            "warning_orange": "#f59e0b",
            "error_red": "#ef4444",
            "text_dark": "#1f2937",
            "text_light": "#6b7280",
            "background_light": "#f8fafc",
            "background_white": "#ffffff",
            "border_light": "#e5e7eb"
        }
    
    def _get_base_style(self) -> str:
        """获取基础样式"""
        return """
        :root {
            --primary-blue: #2563eb;
            --success-green: #10b981;
            --warning-orange: #f59e0b;
            --error-red: #ef4444;
            --text-dark: #1f2937;
            --text-light: #6b7280;
            --bg-light: #f8fafc;
            --bg-white: #ffffff;
            --border-light: #e5e7eb;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 
                         'Helvetica Neue', Arial, sans-serif;
            width: 448px;
            height: 597px;
            overflow: hidden;
            background: var(--bg-white);
            color: var(--text-dark);
            line-height: 1.6;
        }
        
        .redcube-container {
            width: 100%;
            height: 100%;
            position: relative;
            display: flex;
            flex-direction: column;
        }
        
        .redcube-header {
            padding: 1.5rem 1.5rem 1rem;
            text-align: center;
        }
        
        .redcube-content {
            flex: 1;
            padding: 0 1.5rem;
            overflow-y: auto;
        }
        
        .redcube-footer {
            padding: 1rem 1.5rem;
            text-align: center;
            border-top: 1px solid var(--border-light);
            background: var(--bg-light);
        }
        
        .redcube-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-blue);
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        .redcube-subtitle {
            font-size: 1rem;
            color: var(--text-light);
            margin-bottom: 1rem;
        }
        
        .redcube-card {
            background: var(--bg-white);
            border-radius: 12px;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-light);
            overflow: hidden;
        }
        
        .redcube-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }
        
        .badge-blue { background: var(--primary-blue); color: white; }
        .badge-green { background: var(--success-green); color: white; }
        .badge-orange { background: var(--warning-orange); color: white; }
        .badge-red { background: var(--error-red); color: white; }
        
        .redcube-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            font-size: 1rem;
            margin-right: 0.5rem;
        }
        
        .icon-blue { background: var(--primary-blue); color: white; }
        .icon-green { background: var(--success-green); color: white; }
        .icon-orange { background: var(--warning-orange); color: white; }
        .icon-red { background: var(--error-red); color: white; }
        
        .gradient-bg {
            background: linear-gradient(135deg, var(--bg-light) 0%, #e2e8f0 100%);
        }
        
        .gradient-blue {
            background: linear-gradient(135deg, var(--primary-blue) 0%, #3b82f6 100%);
        }
        
        .gradient-green {
            background: linear-gradient(135deg, var(--success-green) 0%, #34d399 100%);
        }
        
        .text-center { text-align: center; }
        .text-left { text-align: left; }
        .text-right { text-align: right; }
        
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-3 { margin-bottom: 0.75rem; }
        .mb-4 { margin-bottom: 1rem; }
        .mb-6 { margin-bottom: 1.5rem; }
        
        .p-2 { padding: 0.5rem; }
        .p-3 { padding: 0.75rem; }
        .p-4 { padding: 1rem; }
        .p-6 { padding: 1.5rem; }
        
        .flex { display: flex; }
        .flex-col { flex-direction: column; }
        .items-center { align-items: center; }
        .justify-center { justify-content: center; }
        .justify-between { justify-content: space-between; }
        
        .grid { display: grid; }
        .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        .grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .gap-2 { gap: 0.5rem; }
        .gap-4 { gap: 1rem; }
        """
    
    def generate_cover_page(self, data: dict) -> str:
        """生成封面页模板"""
        title = data.get("title", "内容标题")
        subtitle = data.get("subtitle", "副标题描述")
        tags = data.get("tags", ["干货分享", "实用技巧"])
        author = data.get("author", "专业分享者")
        icon = data.get("icon", "🎯")
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{self.base_style}</style>
    <style>
        .cover-container {{
            height: 100%;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
            overflow: hidden;
        }}
        
        .cover-main {{
            background: white;
            border-radius: 20px;
            padding: 2.5rem 2rem;
            text-align: center;
            box-shadow: var(--shadow-xl);
            width: 85%;
            position: relative;
            z-index: 2;
        }}
        
        .cover-main::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-blue), var(--warning-orange));
            border-radius: 20px 20px 0 0;
        }}
        
        .cover-icon {{
            font-size: 4rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(45deg, var(--primary-blue), var(--success-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
        }}
        
        .cover-title {{
            font-size: 2rem;
            font-weight: 800;
            color: var(--primary-blue);
            margin-bottom: 1rem;
            line-height: 1.1;
            letter-spacing: -0.025em;
        }}
        
        .cover-subtitle {{
            font-size: 1.1rem;
            color: var(--text-light);
            margin-bottom: 2rem;
            line-height: 1.4;
        }}
        
        .cover-tags {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 2rem;
        }}
        
        .cover-tag {{
            background: linear-gradient(45deg, var(--primary-blue), var(--success-green));
            color: white;
            padding: 0.4rem 1rem;
            border-radius: 25px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .cover-author {{
            font-size: 0.9rem;
            color: var(--text-light);
            font-weight: 500;
        }}
        
        .cover-author::before {{
            content: '@';
            margin-right: 0.25rem;
            color: var(--primary-blue);
        }}
        
        .decorative-circle {{
            position: absolute;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            opacity: 0.1;
            z-index: 1;
        }}
        
        .circle-1 {{
            background: var(--primary-blue);
            top: -60px;
            right: -60px;
        }}
        
        .circle-2 {{
            background: var(--success-green);
            bottom: -60px;
            left: -60px;
        }}
        
        .brand-mark {{
            position: absolute;
            bottom: 1rem;
            right: 1rem;
            font-size: 0.7rem;
            color: var(--text-light);
            opacity: 0.6;
        }}
    </style>
</head>
<body>
    <div class="cover-container">
        <div class="decorative-circle circle-1"></div>
        <div class="decorative-circle circle-2"></div>
        
        <div class="cover-main">
            <div class="cover-icon">{icon}</div>
            <h1 class="cover-title">{title}</h1>
            <p class="cover-subtitle">{subtitle}</p>
            
            <div class="cover-tags">
                {' '.join([f'<span class="cover-tag">{tag}</span>' for tag in tags])}
            </div>
            
            <div class="cover-author">{author}</div>
        </div>
        
        <div class="brand-mark">RedCube AI</div>
    </div>
</body>
</html>"""
    
    def generate_content_page(self, data: dict) -> str:
        """生成内容页模板"""
        title = data.get("title", "内容标题")
        page_number = data.get("page_number", 2)
        content_items = data.get("content_items", [
            {"icon": "✅", "title": "要点一", "description": "详细描述内容"},
            {"icon": "⚡", "title": "要点二", "description": "详细描述内容"},
            {"icon": "🎯", "title": "要点三", "description": "详细描述内容"}
        ])
        tip_text = data.get("tip_text", "重要提示信息")
        
        content_html = ""
        for item in content_items:
            content_html += f"""
            <div class="content-item">
                <div class="item-icon">{item.get('icon', '•')}</div>
                <div class="item-content">
                    <div class="item-title">{item.get('title', '')}</div>
                    <div class="item-description">{item.get('description', '')}</div>
                </div>
            </div>"""
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{self.base_style}</style>
    <style>
        .content-page {{
            background: var(--bg-white);
            padding: 2rem 1.5rem;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        
        .page-header {{
            text-align: center;
            margin-bottom: 2rem;
            position: relative;
        }}
        
        .page-number {{
            position: absolute;
            top: -0.5rem;
            right: 0;
            background: var(--success-green);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            font-weight: 700;
            box-shadow: var(--shadow-md);
        }}
        
        .page-title {{
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--success-green);
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }}
        
        .title-decoration {{
            width: 80px;
            height: 3px;
            background: linear-gradient(90deg, var(--success-green), var(--primary-blue));
            margin: 0 auto;
            border-radius: 2px;
        }}
        
        .content-main {{
            flex: 1;
            overflow-y: auto;
        }}
        
        .content-item {{
            display: flex;
            align-items: flex-start;
            background: linear-gradient(135deg, #f0fdf4, #ffffff);
            border: 1px solid #d1fae5;
            border-left: 4px solid var(--success-green);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow-sm);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .content-item:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }}
        
        .item-icon {{
            background: var(--success-green);
            color: white;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            margin-right: 1rem;
            flex-shrink: 0;
            box-shadow: var(--shadow-sm);
        }}
        
        .item-content {{
            flex: 1;
        }}
        
        .item-title {{
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--text-dark);
            margin-bottom: 0.5rem;
        }}
        
        .item-description {{
            color: var(--text-light);
            font-size: 0.95rem;
            line-height: 1.5;
        }}
        
        .tip-section {{
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            border: 2px solid var(--warning-orange);
            border-radius: 12px;
            padding: 1.2rem;
            margin-top: 1.5rem;
            position: relative;
            box-shadow: var(--shadow-sm);
        }}
        
        .tip-section::before {{
            content: '💡';
            position: absolute;
            top: -12px;
            left: 1.5rem;
            background: var(--warning-orange);
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
        }}
        
        .tip-text {{
            color: #92400e;
            font-weight: 600;
            font-size: 0.9rem;
            line-height: 1.4;
            margin-top: 0.5rem;
        }}
        
        .progress-bar {{
            position: absolute;
            bottom: 0;
            left: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--success-green), var(--primary-blue));
            width: {(page_number / 6) * 100}%;
            border-radius: 0 2px 0 0;
        }}
    </style>
</head>
<body>
    <div class="content-page">
        <div class="page-header">
            <div class="page-number">{page_number}</div>
            <h1 class="page-title">{title}</h1>
            <div class="title-decoration"></div>
        </div>
        
        <div class="content-main">
            {content_html}
            
            <div class="tip-section">
                <div class="tip-text">{tip_text}</div>
            </div>
        </div>
        
        <div class="progress-bar"></div>
    </div>
</body>
</html>"""
    
    def generate_comparison_page(self, data: dict) -> str:
        """生成对比页模板"""
        title = data.get("title", "对比分析")
        page_number = data.get("page_number", 5)
        wrong_items = data.get("wrong_items", ["错误做法1", "错误做法2", "错误做法3"])
        right_items = data.get("right_items", ["正确做法1", "正确做法2", "正确做法3"])
        memory_tip = data.get("memory_tip", "记忆要点")
        
        wrong_html = ""
        for item in wrong_items:
            wrong_html += f'<div class="comparison-item"><span class="item-bullet">×</span><span>{item}</span></div>'
        
        right_html = ""
        for item in right_items:
            right_html += f'<div class="comparison-item"><span class="item-bullet">✓</span><span>{item}</span></div>'
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{self.base_style}</style>
    <style>
        .comparison-page {{
            background: var(--bg-light);
            padding: 1.5rem;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        
        .page-header {{
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        
        .page-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 0.5rem;
        }}
        
        .page-subtitle {{
            font-size: 0.9rem;
            color: var(--text-light);
        }}
        
        .comparison-container {{
            flex: 1;
            display: grid;
            grid-template-columns: 1fr;
            gap: 1rem;
            overflow-y: auto;
        }}
        
        .comparison-section {{
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow-lg);
            position: relative;
            border: 3px solid transparent;
        }}
        
        .wrong-section {{
            border-color: var(--error-red);
            background: linear-gradient(135deg, #fef2f2, white);
        }}
        
        .right-section {{
            border-color: var(--success-green);
            background: linear-gradient(135deg, #f0fdf4, white);
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            margin-bottom: 1.2rem;
        }}
        
        .section-icon {{
            width: 3rem;
            height: 3rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-right: 1rem;
            box-shadow: var(--shadow-md);
        }}
        
        .wrong-section .section-icon {{
            background: var(--error-red);
            color: white;
        }}
        
        .right-section .section-icon {{
            background: var(--success-green);
            color: white;
        }}
        
        .section-title {{
            font-weight: 700;
            font-size: 1.2rem;
        }}
        
        .wrong-section .section-title {{
            color: var(--error-red);
        }}
        
        .right-section .section-title {{
            color: var(--success-green);
        }}
        
        .comparison-content {{
            font-size: 0.9rem;
            line-height: 1.6;
        }}
        
        .comparison-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 0.8rem;
            padding: 0.8rem;
            border-radius: 8px;
            transition: background-color 0.2s ease;
        }}
        
        .wrong-section .comparison-item {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 3px solid var(--error-red);
        }}
        
        .right-section .comparison-item {{
            background: rgba(16, 185, 129, 0.1);
            border-left: 3px solid var(--success-green);
        }}
        
        .comparison-item:hover {{
            background: rgba(0, 0, 0, 0.05);
        }}
        
        .item-bullet {{
            font-weight: 700;
            font-size: 1.1rem;
            margin-right: 0.8rem;
            flex-shrink: 0;
        }}
        
        .wrong-section .item-bullet {{
            color: var(--error-red);
        }}
        
        .right-section .item-bullet {{
            color: var(--success-green);
        }}
        
        .memory-section {{
            background: linear-gradient(135deg, var(--warning-orange), #fbbf24);
            color: white;
            padding: 1rem;
            border-radius: 20px;
            text-align: center;
            margin-top: 1rem;
            box-shadow: var(--shadow-lg);
            position: relative;
        }}
        
        .memory-section::before {{
            content: '🧠';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
        }}
        
        .memory-text {{
            font-weight: 600;
            font-size: 0.9rem;
            line-height: 1.4;
            margin-top: 0.5rem;
        }}
    </style>
</head>
<body>
    <div class="comparison-page">
        <div class="page-header">
            <h1 class="page-title">{title}</h1>
            <p class="page-subtitle">对比学习，避免踩坑</p>
        </div>
        
        <div class="comparison-container">
            <div class="comparison-section wrong-section">
                <div class="section-header">
                    <div class="section-icon">❌</div>
                    <h3 class="section-title">错误做法</h3>
                </div>
                <div class="comparison-content">
                    {wrong_html}
                </div>
            </div>
            
            <div class="comparison-section right-section">
                <div class="section-header">
                    <div class="section-icon">✅</div>
                    <h3 class="section-title">正确做法</h3>
                </div>
                <div class="comparison-content">
                    {right_html}
                </div>
            </div>
        </div>
        
        <div class="memory-section">
            <div class="memory-text">{memory_tip}</div>
        </div>
    </div>
</body>
</html>"""
    
    def generate_final_page(self, data: dict) -> str:
        """生成结尾页模板"""
        title = data.get("title", "总结与行动")
        subtitle = data.get("subtitle", "感谢阅读，一起成长")
        key_points = data.get("key_points", ["要点1", "要点2", "要点3", "要点4"])
        cta_text = data.get("cta_text", "觉得有用请点赞收藏！")
        cta_action = data.get("cta_action", "评论区分享你的经验～")
        author = data.get("author", "专业分享者")
        celebration_icon = data.get("celebration_icon", "🎯")
        
        points_html = ""
        for point in key_points:
            points_html += f'<li>{point}</li>'
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{self.base_style}</style>
    <style>
        .final-page {{
            background: linear-gradient(135deg, #faf5ff, #f3e8ff);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 2rem 1.5rem;
            position: relative;
            overflow: hidden;
        }}
        
        .final-container {{
            background: white;
            border-radius: 24px;
            padding: 2.5rem 2rem;
            box-shadow: var(--shadow-xl);
            width: 100%;
            max-width: 360px;
            position: relative;
            z-index: 2;
        }}
        
        .final-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #8b5cf6, #a78bfa);
            border-radius: 24px 24px 0 0;
        }}
        
        .celebration-icon {{
            font-size: 4.5rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(45deg, #8b5cf6, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 4px 8px rgba(139, 92, 246, 0.3));
        }}
        
        .final-title {{
            font-size: 2rem;
            font-weight: 800;
            color: #8b5cf6;
            margin-bottom: 1rem;
            line-height: 1.1;
            letter-spacing: -0.025em;
        }}
        
        .final-subtitle {{
            font-size: 1rem;
            color: var(--text-light);
            margin-bottom: 2rem;
            line-height: 1.4;
        }}
        
        .key-points-section {{
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border: 2px solid #e2e8f0;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            text-align: left;
        }}
        
        .points-header {{
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .points-icon {{
            background: linear-gradient(45deg, #8b5cf6, #a78bfa);
            color: white;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            margin-right: 0.75rem;
        }}
        
        .points-title {{
            font-weight: 700;
            color: #8b5cf6;
            font-size: 1rem;
        }}
        
        .points-list {{
            list-style: none;
            font-size: 0.9rem;
            color: var(--text-dark);
            line-height: 1.6;
        }}
        
        .points-list li {{
            margin-bottom: 0.5rem;
            display: flex;
            align-items: flex-start;
        }}
        
        .points-list li::before {{
            content: '✨';
            margin-right: 0.5rem;
            color: #8b5cf6;
            font-size: 0.9rem;
            margin-top: 0.1rem;
            flex-shrink: 0;
        }}
        
        .cta-section {{
            background: linear-gradient(135deg, #8b5cf6, #a78bfa);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow-lg);
        }}
        
        .cta-main {{
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }}
        
        .cta-action {{
            font-size: 0.9rem;
            opacity: 0.95;
            line-height: 1.4;
        }}
        
        .author-section {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            font-size: 0.9rem;
            color: var(--text-light);
        }}
        
        .author-name {{
            font-weight: 600;
        }}
        
        .follow-button {{
            background: var(--warning-orange);
            color: white;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: transform 0.2s ease;
            box-shadow: var(--shadow-sm);
        }}
        
        .follow-button:hover {{
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}
        
        .decorative-elements {{
            position: absolute;
            top: 10%;
            right: 10%;
            font-size: 2rem;
            opacity: 0.1;
            color: #8b5cf6;
            z-index: 1;
            animation: float 3s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        .brand-signature {{
            position: absolute;
            bottom: 1rem;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.7rem;
            color: var(--text-light);
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="final-page">
        <div class="decorative-elements">🎉✨🚀</div>
        
        <div class="final-container">
            <div class="celebration-icon">{celebration_icon}</div>
            
            <h1 class="final-title">{title}</h1>
            <p class="final-subtitle">{subtitle}</p>
            
            <div class="key-points-section">
                <div class="points-header">
                    <div class="points-icon">🔥</div>
                    <div class="points-title">核心要点回顾</div>
                </div>
                <ul class="points-list">
                    {points_html}
                </ul>
            </div>
            
            <div class="cta-section">
                <div class="cta-main">{cta_text}</div>
                <div class="cta-action">{cta_action}</div>
            </div>
            
            <div class="author-section">
                <span class="author-name">@ {author}</span>
                <button class="follow-button">+ 关注</button>
            </div>
        </div>
        
        <div class="brand-signature">Powered by RedCube AI</div>
    </div>
</body>
</html>"""

# 模板系统单例
redcube_templates = RedCubeTemplateSystem() 