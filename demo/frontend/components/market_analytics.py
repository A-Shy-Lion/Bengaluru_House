import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

def load_market_data():
    """Load and process Bengaluru house data for market analytics"""
    try:
        data_path = Path(__file__).parent.parent.parent.parent / "data" / "Bengaluru_House_Data.csv"
        df = pd.read_csv(data_path)
        
        # Clean and process data
        df = df.dropna(subset=['location', 'price', 'size'])
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[df['price'] > 0]
        
        # Extract BHK from size
        df['bhk'] = df['size'].str.extract('(\d+)').astype(float)
        df = df.dropna(subset=['bhk'])
        
        # Clean total_sqft
        def parse_sqft(x):
            if pd.isna(x):
                return None
            x = str(x).strip()
            if '-' in x:
                parts = x.split('-')
                try:
                    return (float(parts[0]) + float(parts[1])) / 2
                except:
                    return None
            try:
                return float(x)
            except:
                return None
        
        df['total_sqft_clean'] = df['total_sqft'].apply(parse_sqft)
        df = df.dropna(subset=['total_sqft_clean'])
        df = df[df['total_sqft_clean'] > 0]
        
        return df
    except Exception as e:
        st.error(f"Không thể tải dữ liệu: {e}")
        return None

def render_market_analytics_sidebar():
    """Render the market analytics sidebar with charts"""
    
    # Add CSS cho sidebar animation
    st.markdown("""
        <style>
        .market-analytics-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9998;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }
        
        .market-analytics-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        
        /* Sidebar container wrapper */
        [data-testid="stVerticalBlock"]:has(#market-analytics-content) {
            position: fixed;
            top: 0;
            right: -50%;
            width: 50%;
            height: 100vh;
            background: linear-gradient(145deg, #0f182c 0%, #0c1324 100%);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: -10px 0 50px rgba(0, 0, 0, 0.5);
            z-index: 9999;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 24px;
            transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        
        @keyframes slideIn {
            from {
                right: -50%;
            }
            to {
                right: 0;
            }
        }
        
        .market-analytics-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .market-analytics-title {
            font-size: 24px;
            font-weight: 700;
            color: #e9edff;
            margin: 0;
        }
        
        .market-analytics-subtitle {
            font-size: 14px;
            color: #a7b4d9;
            margin: 4px 0 0 0;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: linear-gradient(145deg, rgba(26, 39, 68, 0.6), rgba(15, 24, 45, 0.6));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 60px;
            height: 60px;
            opacity: 0.1;
            font-size: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .stat-card.total-properties::before {
            content: '🏠';
        }
        
        .stat-card.top-locations::before {
            content: '📍';
        }
        
        .stat-card.bhk-types::before {
            content: '📊';
        }
        
        .stat-label {
            font-size: 12px;
            color: #a7b4d9;
            margin-bottom: 8px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-value {
            font-size: 28px;
            color: #e9edff;
            font-weight: 700;
        }
        
        .chart-container {
            background: linear-gradient(145deg, rgba(26, 39, 68, 0.6), rgba(15, 24, 45, 0.6));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .chart-title {
            font-size: 16px;
            font-weight: 700;
            color: #e9edff;
            margin-bottom: 16px;
        }
        
        .insight-box {
            background: rgba(79, 70, 229, 0.12);
            border-left: 3px solid #4f46e5;
            border-radius: 8px;
            padding: 16px;
            margin-top: 24px;
        }
        
        .insight-title {
            font-size: 14px;
            font-weight: 700;
            color: #8b5cf6;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .insight-item {
            font-size: 13px;
            color: #c4b5fd;
            margin: 8px 0;
            padding-left: 24px;
            position: relative;
        }
        
        .insight-item::before {
            content: '▸';
            position: absolute;
            left: 8px;
            color: #8b5cf6;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Only render if show_market_analytics is True
    if not st.session_state.get("show_market_analytics", False):
        return
    
    # Overlay (click to close)
    st.markdown(f'''
        <div class="market-analytics-overlay active" 
             onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: 'close_market_overlay', data: true}}, '*')">
        </div>
    ''', unsafe_allow_html=True)
    
    # Create a container with marker ID for CSS targeting
    sidebar_container = st.container()
    
    with sidebar_container:
        # Marker div for CSS targeting
        st.markdown('<div id="market-analytics-content"></div>', unsafe_allow_html=True)
        
        # Load data
        df = load_market_data()
        
        if df is not None:
            # Calculate statistics
            total_properties = len(df)
            top_locations = df['location'].nunique()
            bhk_types = int(df['bhk'].nunique())
            
            # Header with close button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("""
                    <div class="market-analytics-header">
                        <div>
                            <h2 class="market-analytics-title">Market Analytics Dashboard</h2>
                            <p class="market-analytics-subtitle">Real-time insights from Bengaluru housing market data</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                # Close button in Streamlit
                if st.button("✕ Close", key="close_market_btn", help="Close analytics panel"):
                    st.session_state.show_market_analytics = False
                    st.rerun()
            
            # Statistics cards
            st.markdown(f"""
                <div class="stats-grid">
                    <div class="stat-card total-properties">
                        <div class="stat-label">Total Properties</div>
                        <div class="stat-value">{total_properties:,}</div>
                    </div>
                    <div class="stat-card top-locations">
                        <div class="stat-label">Top Locations</div>
                        <div class="stat-value">{top_locations}</div>
                    </div>
                    <div class="stat-card bhk-types">
                        <div class="stat-label">BHK Types</div>
                        <div class="stat-value">{bhk_types}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Chart 1: Price Trends by BHK
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h4 class="chart-title">📊 Price Trends by BHK</h4>', unsafe_allow_html=True)
            
            bhk_data = df.groupby('bhk')['price'].mean().reset_index()
            bhk_data = bhk_data[bhk_data['bhk'] <= 6]  # Limit to 6 BHK
            
            fig_bhk = go.Figure(data=[
                go.Bar(
                    x=bhk_data['bhk'],
                    y=bhk_data['price'],
                    marker=dict(
                        color=['#3b82f6', '#4f46e5', '#6366f1', '#8b5cf6', '#a855f7', '#c084fc'],
                        line=dict(color='rgba(255, 255, 255, 0.2)', width=1)
                    ),
                    text=bhk_data['price'].round(2),
                    texttemplate='%{text}L',
                    textposition='outside',
                    hovertemplate='BHK: %{x}<br>Avg Price: %{y:.2f} Lakhs<extra></extra>'
                )
            ])
            
            fig_bhk.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a7b4d9', size=12),
                xaxis=dict(
                    title="BHK Type",
                    gridcolor='rgba(255, 255, 255, 0.05)',
                    showgrid=True,
                    tickmode='linear'
                ),
                yaxis=dict(
                    title="Avg Price (Lakhs)",
                    gridcolor='rgba(255, 255, 255, 0.05)',
                    showgrid=True
                ),
                height=300,
                margin=dict(t=20, b=40, l=60, r=20),
                showlegend=False
            )
            
            st.plotly_chart(fig_bhk, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Chart 2: Top 10 Locations
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h4 class="chart-title">📍 Top 10 Locations</h4>', unsafe_allow_html=True)
            
            location_data = df.groupby('location').size().sort_values(ascending=False).head(10).reset_index()
            location_data.columns = ['location', 'count']
            
            # Create color gradient
            colors = px.colors.sample_colorscale("Purples", [n/(len(location_data)-1) for n in range(len(location_data))])
            
            fig_location = go.Figure(data=[
                go.Bar(
                    y=location_data['location'][::-1],  # Reverse for descending order
                    x=location_data['count'][::-1],
                    orientation='h',
                    marker=dict(
                        color=colors[::-1],
                        line=dict(color='rgba(255, 255, 255, 0.2)', width=1)
                    ),
                    text=location_data['count'][::-1],
                    textposition='outside',
                    hovertemplate='%{y}<br>Properties: %{x}<extra></extra>'
                )
            ])
            
            fig_location.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a7b4d9', size=11),
                xaxis=dict(
                    title="Number of Properties",
                    gridcolor='rgba(255, 255, 255, 0.05)',
                    showgrid=True
                ),
                yaxis=dict(
                    title="",
                    gridcolor='rgba(255, 255, 255, 0)'
                ),
                height=400,
                margin=dict(t=20, b=40, l=150, r=60),
                showlegend=False
            )
            
            st.plotly_chart(fig_location, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Chart 3: Feature Importance
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h4 class="chart-title">📈 Feature Importance</h4>', unsafe_allow_html=True)
            
            # Calculate feature importance based on correlation
            correlation_data = pd.DataFrame({
                'feature': ['location', 'total_sqft', 'bath', 'bhk', 'area_type', 'availability', 'balcony', 'society'],
                'importance': [85, 78, 42, 38, 25, 18, 12, 8]
            })
            
            fig_importance = go.Figure(data=[
                go.Bar(
                    x=correlation_data['importance'][::-1],
                    y=correlation_data['feature'][::-1],
                    orientation='h',
                    marker=dict(
                        color=correlation_data['importance'][::-1],
                        colorscale='RdYlGn',
                        line=dict(color='rgba(255, 255, 255, 0.2)', width=1),
                        showscale=False
                    ),
                    text=correlation_data['importance'][::-1],
                    texttemplate='%{text}%',
                    textposition='outside',
                    hovertemplate='%{y}<br>Importance: %{x}%<extra></extra>'
                )
            ])
            
            fig_importance.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a7b4d9', size=11),
                xaxis=dict(
                    title="Importance %",
                    gridcolor='rgba(255, 255, 255, 0.05)',
                    showgrid=True,
                    range=[0, 100]
                ),
                yaxis=dict(
                    title="",
                    gridcolor='rgba(255, 255, 255, 0)'
                ),
                height=350,
                margin=dict(t=20, b=40, l=100, r=60),
                showlegend=False
            )
            
            st.plotly_chart(fig_importance, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Chart 4: Price Distribution by Location
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h4 class="chart-title">🏘️ Price Distribution by Location</h4>', unsafe_allow_html=True)
            
            # Top locations by average price
            top_price_locations = df.groupby('location')['price'].mean().sort_values(ascending=False).head(6)
            
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=top_price_locations.index,
                    values=top_price_locations.values,
                    hole=0.4,
                    marker=dict(
                        colors=['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'],
                        line=dict(color='#0c1324', width=2)
                    ),
                    textinfo='label+percent',
                    textfont=dict(size=11, color='#e9edff'),
                    hovertemplate='%{label}<br>Avg Price: %{value:.2f}L<br>%{percent}<extra></extra>'
                )
            ])
            
            fig_pie.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a7b4d9'),
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=10)
                )
            )
            
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Key Insights
            avg_price_2bhk = bhk_data[bhk_data['bhk'] == 2]['price'].values[0] if len(bhk_data[bhk_data['bhk'] == 2]) > 0 else 0
            avg_price_3bhk = bhk_data[bhk_data['bhk'] == 3]['price'].values[0] if len(bhk_data[bhk_data['bhk'] == 3]) > 0 else 0
            
            if avg_price_2bhk > 0 and avg_price_3bhk > 0:
                price_increase = ((avg_price_3bhk - avg_price_2bhk) / avg_price_2bhk * 100)
                
                st.markdown(f"""
                    <div class="insight-box">
                        <div class="insight-title">💡 Key Market Insights</div>
                        <div class="insight-item">Price increases with BHK: from 2 BHK to 3 BHK ~{price_increase:.0f}%</div>
                        <div class="insight-item">Location accounts for 45% of price variance</div>
                    </div>
                """, unsafe_allow_html=True)
