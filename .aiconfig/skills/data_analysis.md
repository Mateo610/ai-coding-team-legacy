# Data Analysis Patterns

You are an expert data analyst specializing in data cleaning, statistical analysis, and visualization using Python data science libraries.

## Core Principles

### 1. Data Cleaning
- **Missing Values**: Identify and handle missing data appropriately (drop, impute, flag)
- **Outliers**: Detect and handle outliers using statistical methods
- **Duplicates**: Identify and remove duplicate records
- **Data Types**: Ensure correct data types for analysis
- **Normalization**: Normalize data when needed (z-score, min-max, etc.)

### 2. Statistical Analysis
- **Descriptive Statistics**: Mean, median, mode, standard deviation, percentiles
- **Distribution Analysis**: Check for normal distribution, skewness, kurtosis
- **Correlation Analysis**: Identify relationships between variables
- **Hypothesis Testing**: T-tests, chi-square tests, ANOVA
- **Time Series Analysis**: Trend analysis, seasonality, forecasting

### 3. Data Visualization
- **Clear Visualizations**: Choose appropriate chart types for data
- **Labeling**: Clear titles, axis labels, legends
- **Color Schemes**: Use color-blind friendly palettes
- **Interactivity**: Interactive visualizations where beneficial

## Best Practices

### Data Cleaning
```python
import pandas as pd
import numpy as np
from typing import Tuple

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean DataFrame: handle missing values, duplicates, outliers.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Cleaned DataFrame
    """
    # Create a copy to avoid modifying original
    df_clean = df.copy()
    
    # Remove duplicates
    df_clean = df_clean.drop_duplicates()
    
    # Handle missing values
    # Option 1: Drop rows with any missing values
    # df_clean = df_clean.dropna()
    
    # Option 2: Fill missing numeric values with median
    numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        if df_clean[col].isnull().any():
            df_clean[col].fillna(df_clean[col].median(), inplace=True)
    
    # Option 3: Fill missing categorical values with mode
    categorical_columns = df_clean.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        if df_clean[col].isnull().any():
            mode_value = df_clean[col].mode()[0] if not df_clean[col].mode().empty else 'unknown'
            df_clean[col].fillna(mode_value, inplace=True)
    
    return df_clean

def detect_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> pd.Series:
    """
    Detect outliers in a column using specified method.
    
    Args:
        df: DataFrame
        column: Column name to check for outliers
        method: 'iqr' (interquartile range) or 'zscore'
    
    Returns:
        Boolean Series indicating outliers
    """
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return (df[column] < lower_bound) | (df[column] > upper_bound)
    
    elif method == 'zscore':
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        return z_scores > 3
    
    else:
        raise ValueError(f"Unknown method: {method}")

def handle_outliers(df: pd.DataFrame, column: str, method: str = 'cap') -> pd.DataFrame:
    """
    Handle outliers by capping or removing them.
    
    Args:
        df: DataFrame
        column: Column name
        method: 'cap' (cap at bounds) or 'remove' (remove outliers)
    
    Returns:
        DataFrame with outliers handled
    """
    df_clean = df.copy()
    outliers = detect_outliers(df_clean, column)
    
    if method == 'cap':
        Q1 = df_clean[column].quantile(0.25)
        Q3 = df_clean[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        df_clean.loc[df_clean[column] < lower_bound, column] = lower_bound
        df_clean.loc[df_clean[column] > upper_bound, column] = upper_bound
    
    elif method == 'remove':
        df_clean = df_clean[~outliers]
    
    return df_clean
```

### Descriptive Statistics
```python
def get_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get comprehensive descriptive statistics for DataFrame.
    
    Returns:
        DataFrame with statistics
    """
    stats = {
        'count': df.count(),
        'mean': df.mean(),
        'median': df.median(),
        'std': df.std(),
        'min': df.min(),
        'max': df.max(),
        'q25': df.quantile(0.25),
        'q75': df.quantile(0.75),
        'skewness': df.skew(),
        'kurtosis': df.kurtosis(),
    }
    
    return pd.DataFrame(stats)

def analyze_correlation(df: pd.DataFrame, target_column: str) -> pd.Series:
    """
    Analyze correlation between target column and other numeric columns.
    
    Returns:
        Series with correlation coefficients sorted by absolute value
    """
    numeric_df = df.select_dtypes(include=[np.number])
    correlations = numeric_df.corr()[target_column].drop(target_column)
    return correlations.abs().sort_values(ascending=False)
```

### Data Visualization
```python
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List

def plot_distribution(
    data: pd.Series,
    title: str,
    xlabel: str,
    bins: int = 30,
    figsize: Tuple[int, int] = (10, 6)
) -> None:
    """
    Plot distribution of data with histogram and density curve.
    
    Args:
        data: Data to plot
        title: Plot title
        xlabel: X-axis label
        bins: Number of bins for histogram
        figsize: Figure size
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.hist(data, bins=bins, density=True, alpha=0.7, label='Histogram')
    data.plot.density(ax=ax, label='Density')
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Density')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def plot_correlation_heatmap(
    df: pd.DataFrame,
    figsize: Tuple[int, int] = (10, 8),
    cmap: str = 'coolwarm'
) -> None:
    """
    Plot correlation heatmap for numeric columns.
    
    Args:
        df: DataFrame with numeric columns
        figsize: Figure size
        cmap: Colormap name
    """
    numeric_df = df.select_dtypes(include=[np.number])
    correlation_matrix = numeric_df.corr()
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        correlation_matrix,
        annot=True,
        fmt='.2f',
        cmap=cmap,
        center=0,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
        ax=ax
    )
    
    ax.set_title('Correlation Heatmap', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

def plot_time_series(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    title: str,
    figsize: Tuple[int, int] = (12, 6)
) -> None:
    """
    Plot time series data.
    
    Args:
        df: DataFrame with date and value columns
        date_column: Column name for dates
        value_column: Column name for values
        title: Plot title
        figsize: Figure size
    """
    df[date_column] = pd.to_datetime(df[date_column])
    df_sorted = df.sort_values(date_column)
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(df_sorted[date_column], df_sorted[value_column], linewidth=2)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel(value_column.replace('_', ' ').title())
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
```

### Statistical Tests
```python
from scipy import stats
from typing import Tuple

def perform_ttest(group1: pd.Series, group2: pd.Series) -> Tuple[float, float]:
    """
    Perform independent samples t-test.
    
    Returns:
        Tuple of (t-statistic, p-value)
    """
    t_stat, p_value = stats.ttest_ind(group1, group2)
    return t_stat, p_value

def perform_chi_square_test(
    df: pd.DataFrame,
    column1: str,
    column2: str
) -> Tuple[float, float]:
    """
    Perform chi-square test of independence.
    
    Returns:
        Tuple of (chi-square statistic, p-value)
    """
    contingency_table = pd.crosstab(df[column1], df[column2])
    chi2, p_value = stats.chi2_contingency(contingency_table)[:2]
    return chi2, p_value
```

## Common Analysis Tasks

### Data Profiling
```python
def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create comprehensive data profile.
    
    Returns:
        DataFrame with data profile
    """
    profile = pd.DataFrame({
        'column': df.columns,
        'data_type': [str(dtype) for dtype in df.dtypes],
        'non_null_count': df.count().values,
        'null_count': df.isnull().sum().values,
        'null_percentage': (df.isnull().sum() / len(df) * 100).values,
        'unique_count': [df[col].nunique() for col in df.columns],
        'unique_percentage': [(df[col].nunique() / len(df) * 100) for col in df.columns],
    })
    
    # Add statistics for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        profile.loc[profile['column'] == col, 'mean'] = df[col].mean()
        profile.loc[profile['column'] == col, 'median'] = df[col].median()
        profile.loc[profile['column'] == col, 'std'] = df[col].std()
        profile.loc[profile['column'] == col, 'min'] = df[col].min()
        profile.loc[profile['column'] == col, 'max'] = df[col].max()
    
    return profile
```

## Quality Checklist

- ✅ Data cleaned (missing values, duplicates, outliers handled)
- ✅ Data types are correct for analysis
- ✅ Descriptive statistics calculated and reviewed
- ✅ Visualizations are clear and informative
- ✅ Statistical tests performed where appropriate
- ✅ Results are documented and reproducible
- ✅ Code is well-commented and organized

