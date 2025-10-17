# Python Visualization Library for Issuer Due Diligence Reports

## Overview

This document specifies all Python visualization scripts required to create charts and graphs for real estate issuer due diligence reports. All visualizations must match the professional quality and format of institutional credit rating agency reports.

**Required Libraries:**
- `matplotlib`: Core plotting library
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `seaborn` (optional): Enhanced styling
- `datetime`: Date handling

---

## I. Chart Styling and Configuration

### 1. Standard Style Configuration

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

# Global style settings
def configure_chart_style():
    """
    Configure global matplotlib settings for professional report charts.
    """
    plt.style.use('seaborn-v0_8-darkgrid')

    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica'],
        'font.size': 10,
        'axes.labelsize': 10,
        'axes.titlesize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 12,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        'axes.axisbelow': True,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight'
    })


# Color palette (Moody's-style professional colors)
COLORS = {
    'primary': '#003F87',      # Dark blue
    'secondary': '#00A3E0',    # Light blue
    'accent1': '#7AB800',      # Green
    'accent2': '#FF8200',      # Orange
    'accent3': '#6C5B7B',      # Purple
    'gray1': '#333333',        # Dark gray
    'gray2': '#666666',        # Medium gray
    'gray3': '#CCCCCC',        # Light gray
    'negative': '#C8102E',     # Red
    'warning': '#FF8200'       # Orange
}

# Geographic color mapping (for stacked charts)
GEO_COLORS = {
    'Singapore': '#003F87',
    'Australia': '#00A3E0',
    'United States': '#7AB800',
    'United Kingdom/Europe': '#FF8200',
    'Europe': '#FF8200',
    'China': '#6C5B7B'
}
```

### 2. Formatting Utilities

```python
def format_y_axis_currency(ax, unit='millions'):
    """
    Format y-axis as currency.

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to format
    unit : str
        'millions' or 'billions'
    """
    if unit == 'millions':
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, p: f'${x:,.0f}M' if x >= 0 else f'-${abs(x):,.0f}M')
        )
    elif unit == 'billions':
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, p: f'${x:,.1f}B' if x >= 0 else f'-${abs(x):,.1f}B')
        )


def format_y_axis_percentage(ax):
    """
    Format y-axis as percentage.
    """
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, p: f'{x:.0f}%')
    )


def format_y_axis_multiple(ax):
    """
    Format y-axis as multiple (e.g., 7.5x).
    """
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, p: f'{x:.1f}x')
    )


def add_data_labels_bar(ax, bars, format_type='currency', unit='millions'):
    """
    Add data labels on top of bars.

    Parameters:
    -----------
    ax : matplotlib axis
    bars : bar container
    format_type : str
        'currency', 'percentage', 'multiple', or 'number'
    unit : str
        For currency: 'millions' or 'billions'
    """
    for bar in bars:
        height = bar.get_height()

        if format_type == 'currency':
            if unit == 'millions':
                label = f'${height:,.0f}M'
            else:
                label = f'${height:,.1f}B'
        elif format_type == 'percentage':
            label = f'{height:.1f}%'
        elif format_type == 'multiple':
            label = f'{height:.1f}x'
        else:
            label = f'{height:,.0f}'

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            label,
            ha='center',
            va='bottom',
            fontsize=8
        )
```

---

## II. Key Visualization Templates

### 1. Stacked Bar Chart: Asset Values by Geography Over Time

```python
def create_asset_value_by_geography_chart(
    data: pd.DataFrame,
    save_path: str = None
) -> plt.Figure:
    """
    Create stacked bar chart showing asset values by geography over time.

    Matches Exhibit 1 from Moody's template.

    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame with:
        - Index: Time periods (e.g., 'Mar-15', 'Mar-16', etc.)
        - Columns: Geographic regions
        - Values: Asset values in $ billions
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    fig, ax = plt.subplots(figsize=(12, 6))

    # Create stacked bar chart
    data.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        color=[GEO_COLORS.get(col, COLORS['gray2']) for col in data.columns],
        width=0.7,
        edgecolor='white',
        linewidth=0.5
    )

    # Formatting
    ax.set_xlabel('')
    ax.set_ylabel('SGD billions', fontsize=10)
    ax.set_title(
        'Asset values by geography',
        fontsize=11,
        fontweight='bold',
        loc='left'
    )

    # Format y-axis
    format_y_axis_currency(ax, unit='billions')

    # Rotate x-axis labels
    ax.set_xticklabels(data.index, rotation=0, ha='center')

    # Legend
    ax.legend(
        title='',
        loc='upper left',
        ncol=len(data.columns),
        frameon=False,
        fontsize=9
    )

    # Grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

### 2. Line + Bar Combo: Revenue, EBITDA, and EBITDA Margin

```python
def create_revenue_ebitda_chart(
    data: pd.DataFrame,
    save_path: str = None
) -> plt.Figure:
    """
    Create combo chart with revenue and EBITDA bars plus EBITDA margin line.

    Matches Exhibit 3 from Moody's template.

    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame with columns:
        - 'Year': Time periods
        - 'Revenue': Revenue values
        - 'EBITDA': EBITDA values
        - 'EBITDA_Margin': EBITDA margin as percentage
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar width
    x = np.arange(len(data))
    width = 0.35

    # Bars for Revenue and EBITDA
    bars1 = ax1.bar(
        x - width/2,
        data['Revenue'],
        width,
        label='Revenue',
        color=COLORS['primary'],
        alpha=0.8
    )

    bars2 = ax1.bar(
        x + width/2,
        data['EBITDA'],
        width,
        label='EBITDA',
        color=COLORS['secondary'],
        alpha=0.8
    )

    # Left y-axis (currency)
    ax1.set_ylabel('SGD millions', fontsize=10)
    format_y_axis_currency(ax1, unit='millions')
    ax1.tick_params(axis='y')

    # Create second y-axis for margin
    ax2 = ax1.twinx()

    # Line for EBITDA Margin
    line = ax2.plot(
        x,
        data['EBITDA_Margin'],
        color=COLORS['gray1'],
        marker='',
        linewidth=2.5,
        label='EBITDA Margin'
    )

    # Right y-axis (percentage)
    ax2.set_ylabel('EBITDA Margin', fontsize=10)
    format_y_axis_percentage(ax2)
    ax2.tick_params(axis='y')

    # X-axis
    ax1.set_xticks(x)
    ax1.set_xticklabels(data['Year'], rotation=0)
    ax1.set_xlabel('')

    # Title
    ax1.set_title(
        'Earnings will rise, supported by stable operating performance',
        fontsize=11,
        fontweight='bold',
        loc='left'
    )

    # Combined legend
    bars_labels = [bars1, bars2]
    bars_text = ['Revenue (left axis)', 'EBITDA (left axis)']

    ax1.legend(
        bars_labels + line,
        bars_text + ['EBITDA Margin (right axis)'],
        loc='upper left',
        frameon=False,
        fontsize=9
    )

    # Grid
    ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax1.set_axisbelow(True)
    ax1.xaxis.grid(False)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

### 3. Line Chart: Coverage and Leverage Ratios with Threshold Lines

```python
def create_ratio_trend_with_threshold(
    data: pd.DataFrame,
    ratio_name: str,
    threshold_value: float,
    threshold_label: str,
    save_path: str = None
) -> plt.Figure:
    """
    Create line chart showing ratio trend with a threshold/downgrade line.

    Matches Exhibits 4 and 5 from Moody's template.

    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame with columns:
        - 'Year': Time periods
        - 'Ratio': Ratio values
    ratio_name : str
        Name of ratio (e.g., 'EBITDA / Interest Expense')
    threshold_value : float
        Threshold line value (e.g., downgrade factor)
    threshold_label : str
        Label for threshold (e.g., 'Downgrade factor')
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Line for actual ratio
    ax.plot(
        data['Year'],
        data['Ratio'],
        color=COLORS['primary'],
        marker='o',
        markersize=6,
        linewidth=2.5,
        label=ratio_name
    )

    # Threshold line (dashed)
    ax.axhline(
        y=threshold_value,
        color=COLORS['negative'],
        linestyle='--',
        linewidth=2,
        label=threshold_label
    )

    # Formatting
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Determine if this is coverage (higher=better) or leverage (lower=better)
    if 'Coverage' in ratio_name or 'Interest' in ratio_name:
        format_y_axis_multiple(ax)
    else:
        format_y_axis_multiple(ax)

    # Title
    title_map = {
        'EBITDA / Interest Expense': 'Interest coverage ratio will gradually improve as interest rates ease',
        'Net Debt / EBITDA': 'Planned acquisitions and capital spending will keep leverage high'
    }

    ax.set_title(
        title_map.get(ratio_name, f'{ratio_name} trend'),
        fontsize=11,
        fontweight='bold',
        loc='left'
    )

    # Legend
    ax.legend(loc='best', frameon=False, fontsize=9)

    # Grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

### 4. Stacked Bar Chart: Acquisitions, Divestments, and Equity Flows

```python
def create_capital_deployment_chart(
    data: pd.DataFrame,
    save_path: str = None
) -> plt.Figure:
    """
    Create chart showing capital deployment: outflows and inflows by category.

    Matches Exhibit 6 from Moody's template.

    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame with columns:
        - 'Period': Time periods (e.g., 'FYE Mar-16')
        - 'Flow_Type': 'Outflow' or 'Inflow'
        - 'Acquisitions': Acquisition amounts
        - 'Investments': Investment amounts
        - 'Divestments': Divestment proceeds
        - 'Equity': Equity issuances
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    fig, ax = plt.subplots(figsize=(14, 6))

    # Separate outflows and inflows
    outflows = data[data['Flow_Type'] == 'Outflow']
    inflows = data[data['Flow_Type'] == 'Inflow']

    # X positions
    periods = data['Period'].unique()
    x = np.arange(len(periods)) * 2  # Double spacing for outflow/inflow pairs

    width = 0.8

    # Outflow bars (left of each pair)
    outflow_x = x - width/2
    ax.bar(
        outflow_x,
        outflows['Acquisitions'],
        width,
        label='Acquisitions',
        color=COLORS['primary']
    )
    ax.bar(
        outflow_x,
        outflows['Investments'],
        width,
        bottom=outflows['Acquisitions'],
        label='Investments',
        color=COLORS['accent3']
    )

    # Inflow bars (right of each pair)
    inflow_x = x + width/2
    ax.bar(
        inflow_x,
        inflows['Divestments'],
        width,
        label='Divestment proceeds',
        color=COLORS['accent1']
    )
    ax.bar(
        inflow_x,
        inflows['Equity'],
        width,
        bottom=inflows['Divestments'],
        label='Equity issuances',
        color=COLORS['secondary']
    )

    # Formatting
    ax.set_ylabel('SGD millions', fontsize=10)
    format_y_axis_currency(ax, unit='millions')

    ax.set_title(
        'Capital deployment funded with mix of divestments, debt and equity',
        fontsize=11,
        fontweight='bold',
        loc='left'
    )

    # X-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels([f'{p}\nOutflow  Inflow' for p in periods], fontsize=8)

    # Legend
    ax.legend(loc='upper left', ncol=4, frameon=False, fontsize=9)

    # Grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

### 5. Stacked Bar Chart: Debt Maturity Profile

```python
def create_debt_maturity_profile_chart(
    data: pd.DataFrame,
    save_path: str = None
) -> plt.Figure:
    """
    Create stacked bar chart showing debt maturities by year and type.

    Matches Exhibit 10 from Moody's template.

    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame with:
        - Index: Years (e.g., 2025, 2026, etc.)
        - Columns: Debt types (e.g., 'Term Loans', 'Revolvers', 'Bonds', 'Green Debt')
        - Values: Amounts maturing each year
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    fig, ax = plt.subplots(figsize=(12, 6))

    # Define colors for debt types
    debt_colors = {
        'Committed loan facilities': COLORS['primary'],
        'Revolving credit facilities': COLORS['accent2'],
        'Medium term notes': COLORS['secondary'],
        'Green debt': COLORS['accent1']
    }

    # Create stacked bars
    data.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        color=[debt_colors.get(col, COLORS['gray2']) for col in data.columns],
        width=0.7,
        edgecolor='white',
        linewidth=0.5
    )

    # Formatting
    ax.set_ylabel('SGD millions', fontsize=10)
    ax.set_xlabel('')
    format_y_axis_currency(ax, unit='millions')

    ax.set_title(
        'Well-balanced debt maturity profile',
        fontsize=11,
        fontweight='bold',
        loc='left'
    )

    # X-axis
    ax.set_xticklabels(data.index, rotation=0)

    # Legend
    ax.legend(
        title='',
        loc='upper left',
        ncol=2,
        frameon=False,
        fontsize=9
    )

    # Grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

### 6. Dual-Axis Line Chart: Occupancy and WALE Trends

```python
def create_occupancy_wale_chart(
    data: pd.DataFrame,
    save_path: str = None
) -> plt.Figure:
    """
    Create dual-axis chart showing occupancy rate (bars) and WALE (line).

    Matches Exhibit 7 from Moody's template.

    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame with columns:
        - 'Period': Time periods
        - 'Occupancy': Occupancy rate (%)
        - 'WALE': Weighted average lease expiry (years)
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart for occupancy
    x = np.arange(len(data))
    bars = ax1.bar(
        x,
        data['Occupancy'],
        color=COLORS['accent1'],
        alpha=0.7,
        label='Portfolio occupancy (left axis)'
    )

    # Left y-axis (percentage)
    ax1.set_ylabel('Occupancy Rate', fontsize=10)
    format_y_axis_percentage(ax1)
    ax1.set_ylim(80, 100)
    ax1.tick_params(axis='y')

    # Right y-axis for WALE
    ax2 = ax1.twinx()

    line = ax2.plot(
        x,
        data['WALE'],
        color=COLORS['primary'],
        marker='o',
        markersize=5,
        linewidth=2.5,
        label='Portfolio WALE (right axis)'
    )

    ax2.set_ylabel('WALE (Years)', fontsize=10)
    ax2.set_ylim(3.0, 5.0)
    ax2.tick_params(axis='y')

    # X-axis
    ax1.set_xticks(x)
    ax1.set_xticklabels(data['Period'], rotation=0)
    ax1.set_xlabel('')

    # Title
    ax1.set_title(
        'Consistently maintained high occupancy rates and stable WALE',
        fontsize=11,
        fontweight='bold',
        loc='left'
    )

    # Combined legend
    ax1.legend(
        [bars] + line,
        ['Portfolio occupancy (left axis)', 'Portfolio WALE (right axis)'],
        loc='lower left',
        frameon=False,
        fontsize=9
    )

    # Grid
    ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax1.xaxis.grid(False)
    ax1.set_axisbelow(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

---

## III. ESG Visualization

```python
def create_esg_score_visualization(
    overall_score: str,
    e_score: int,
    s_score: int,
    g_score: int,
    save_path: str = None
) -> plt.Figure:
    """
    Create ESG score visualization matching Moody's format.

    Shows overall CIS score and E-S-G component scores.

    Parameters:
    -----------
    overall_score : str
        Overall CIS score (e.g., 'CIS-2')
    e_score : int
        Environmental score (1-5)
    s_score : int
        Social score (1-5)
    g_score : int
        Governance score (1-5)
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    fig = plt.figure(figsize=(10, 4))

    # Create grid
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 2], wspace=0.3)

    # Left: Overall CIS score
    ax1 = fig.add_subplot(gs[0])
    ax1.text(
        0.5, 0.6,
        overall_score,
        fontsize=48,
        fontweight='bold',
        ha='center',
        va='center'
    )
    ax1.text(
        0.5, 0.3,
        'ESG Credit Impact Score',
        fontsize=10,
        ha='center',
        va='center'
    )
    ax1.axis('off')

    # Right: E-S-G breakdown
    ax2 = fig.add_subplot(gs[1])

    categories = ['E\nEnvironmental', 'S\nSocial', 'G\nGovernance']
    scores = [e_score, s_score, g_score]

    # Horizontal bars showing score position
    y_positions = [2, 1, 0]

    for i, (cat, score, y_pos) in enumerate(zip(categories, scores, y_positions)):
        # Background bar (full scale)
        ax2.barh(
            y_pos,
            5,
            height=0.4,
            color=COLORS['gray3'],
            alpha=0.3
        )

        # Score indicator
        ax2.barh(
            y_pos,
            score,
            height=0.4,
            color=COLORS['primary']
        )

        # Category label
        ax2.text(
            -0.5, y_pos,
            cat,
            va='center',
            ha='right',
            fontsize=10,
            fontweight='bold'
        )

        # Score label
        ax2.text(
            5.3, y_pos,
            f'{score}',
            va='center',
            ha='left',
            fontsize=10,
            fontweight='bold'
        )

    ax2.set_xlim(-1, 6)
    ax2.set_ylim(-0.5, 2.5)
    ax2.axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

---

## IV. Peer Comparison Charts

```python
def create_peer_comparison_chart(
    peer_data: pd.DataFrame,
    metrics: List[str],
    issuer_name: str,
    save_path: str = None
) -> plt.Figure:
    """
    Create grouped bar chart comparing issuer to peers on key metrics.

    Parameters:
    -----------
    peer_data : pd.DataFrame
        DataFrame with:
        - Column 'Company': Company names
        - Other columns: Metric values
    metrics : List[str]
        List of metric column names to compare
    issuer_name : str
        Name of the issuer (to highlight)
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(4*n_metrics, 6))

    if n_metrics == 1:
        axes = [axes]

    for idx, metric in enumerate(metrics):
        ax = axes[idx]

        # Get data for this metric
        companies = peer_data['Company'].tolist()
        values = peer_data[metric].tolist()

        # Color issuer differently
        colors = [
            COLORS['accent1'] if comp == issuer_name else COLORS['gray2']
            for comp in companies
        ]

        # Create bar chart
        bars = ax.bar(
            range(len(companies)),
            values,
            color=colors,
            alpha=0.8
        )

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f'{height:.1f}' if 'x' in metric.lower() else f'{height:.1f}%',
                ha='center',
                va='bottom',
                fontsize=8
            )

        # Formatting
        ax.set_xticks(range(len(companies)))
        ax.set_xticklabels(companies, rotation=45, ha='right', fontsize=9)
        ax.set_title(metric, fontsize=10, fontweight='bold')

        # Format y-axis based on metric type
        if 'EBITDA' in metric or 'Debt' in metric:
            format_y_axis_multiple(ax)
        else:
            format_y_axis_percentage(ax)

        ax.yaxis.grid(True, linestyle='--', alpha=0.3)
        ax.set_axisbelow(True)

    plt.suptitle(
        f'Peer Comparison: {issuer_name}',
        fontsize=12,
        fontweight='bold',
        y=1.02
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

---

## V. Forecast Tables with Visualizations

```python
def create_forecast_metrics_table_with_trends(
    historical_data: pd.DataFrame,
    forecast_data: pd.DataFrame,
    save_path: str = None
) -> plt.Figure:
    """
    Create table showing historical and forecast metrics with embedded sparklines.

    Parameters:
    -----------
    historical_data : pd.DataFrame
        Historical data (columns = metrics, index = years)
    forecast_data : pd.DataFrame
        Forecast data (columns = metrics, index = years)
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    plt.Figure : The created figure
    """
    configure_chart_style()

    # Combine historical and forecast
    all_data = pd.concat([historical_data, forecast_data], axis=0)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')

    # Create table
    table_data = []
    table_data.append(['Metric'] + list(all_data.index))

    for metric in all_data.columns:
        row = [metric] + [f'{val:,.0f}' if 'Assets' in metric or 'EBITDA' in metric
                          else f'{val:.1f}%' if '%' in metric
                          else f'{val:.1f}x'
                          for val in all_data[metric]]
        table_data.append(row)

    table = ax.table(
        cellText=table_data,
        cellLoc='center',
        loc='center',
        colWidths=[0.15] + [0.1] * len(all_data.index)
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    # Style header row
    for i in range(len(table_data[0])):
        cell = table[(0, i)]
        cell.set_facecolor(COLORS['primary'])
        cell.set_text_props(weight='bold', color='white')

    # Highlight forecast columns
    forecast_cols = len(historical_data.columns)
    for row in range(1, len(table_data)):
        for col in range(forecast_cols + 1, len(table_data[0])):
            cell = table[(row, col)]
            cell.set_facecolor(COLORS['gray3'])

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig
```

---

## VI. Utility: Save All Charts for Report

```python
def generate_all_report_charts(
    data_dict: Dict[str, pd.DataFrame],
    output_dir: str
) -> Dict[str, str]:
    """
    Generate all standard charts for the report and save to directory.

    Parameters:
    -----------
    data_dict : Dict[str, pd.DataFrame]
        Dictionary with keys:
        - 'asset_values': Data for asset value chart
        - 'revenue_ebitda': Data for revenue/EBITDA chart
        - 'coverage_ratio': Data for coverage ratio chart
        - 'leverage_ratio': Data for leverage ratio chart
        - 'capital_deployment': Data for capital deployment chart
        - 'debt_maturity': Data for debt maturity chart
        - 'occupancy_wale': Data for occupancy/WALE chart
        - 'peer_comparison': Data for peer comparison
    output_dir : str
        Directory to save charts

    Returns:
    --------
    Dict[str, str] : Map of chart names to file paths
    """
    import os

    os.makedirs(output_dir, exist_ok=True)

    chart_paths = {}

    # Asset values by geography
    if 'asset_values' in data_dict:
        path = os.path.join(output_dir, 'exhibit1_asset_values.png')
        create_asset_value_by_geography_chart(data_dict['asset_values'], path)
        chart_paths['asset_values'] = path

    # Revenue and EBITDA
    if 'revenue_ebitda' in data_dict:
        path = os.path.join(output_dir, 'exhibit3_revenue_ebitda.png')
        create_revenue_ebitda_chart(data_dict['revenue_ebitda'], path)
        chart_paths['revenue_ebitda'] = path

    # Coverage ratio
    if 'coverage_ratio' in data_dict:
        path = os.path.join(output_dir, 'exhibit4_coverage_ratio.png')
        create_ratio_trend_with_threshold(
            data_dict['coverage_ratio'],
            'EBITDA / Interest Expense',
            3.25,
            'Downgrade factor',
            path
        )
        chart_paths['coverage_ratio'] = path

    # Leverage ratio
    if 'leverage_ratio' in data_dict:
        path = os.path.join(output_dir, 'exhibit5_leverage_ratio.png')
        create_ratio_trend_with_threshold(
            data_dict['leverage_ratio'],
            'Net Debt / EBITDA',
            8.0,
            'Downgrade factor',
            path
        )
        chart_paths['leverage_ratio'] = path

    # Capital deployment
    if 'capital_deployment' in data_dict:
        path = os.path.join(output_dir, 'exhibit6_capital_deployment.png')
        create_capital_deployment_chart(data_dict['capital_deployment'], path)
        chart_paths['capital_deployment'] = path

    # Debt maturity
    if 'debt_maturity' in data_dict:
        path = os.path.join(output_dir, 'exhibit10_debt_maturity.png')
        create_debt_maturity_profile_chart(data_dict['debt_maturity'], path)
        chart_paths['debt_maturity'] = path

    # Occupancy and WALE
    if 'occupancy_wale' in data_dict:
        path = os.path.join(output_dir, 'exhibit7_occupancy_wale.png')
        create_occupancy_wale_chart(data_dict['occupancy_wale'], path)
        chart_paths['occupancy_wale'] = path

    return chart_paths
```

---

## VII. Notes on Implementation

### Chart Quality Standards

1. **Resolution:** All charts saved at 300 DPI for print quality
2. **Colors:** Professional palette matching institutional standards
3. **Fonts:** Arial/Helvetica sans-serif, consistent sizing
4. **Grid:** Light gray dashed gridlines, axis-below
5. **Labels:** All data points labeled where space permits
6. **Legends:** Frameless, positioned to avoid data obstruction

### Data Preparation

- Ensure data is in proper units before passing to functions
- Handle missing data gracefully (NaN → skip or interpolate)
- Validate date/period formatting for x-axis labels

### Integration with PDF Generation

Charts are saved as PNG files and then embedded in the PDF report using ReportLab (see `report_generation_workflow.md`).

