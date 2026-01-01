"""
Test script to verify all new features are working correctly
"""
import sys
sys.path.append('backend')

import pandas as pd
from helpers import (
    create_smart_visualizations, 
    generate_plot_local, 
    preprocess_dataset
)

# Test 1: Smart Auto-Visualization
print("=" * 60)
print("TEST 1: Smart Auto-Visualization")
print("=" * 60)

# Load test data
df = pd.read_csv('uploads/iris.csv')
print(f"✅ Loaded iris dataset: {df.shape}")

# Generate smart visualizations
plots = create_smart_visualizations(df, max_plots=12)
print(f"✅ Generated {len(plots)} smart visualizations:")
for plot_name, fig in plots:
    print(f"  - {plot_name}")

# Test 2: Seaborn Plots
print("\n" + "=" * 60)
print("TEST 2: Seaborn Plot Types")
print("=" * 60)

seaborn_plots = ['pairplot', 'kdeplot', 'countplot']
for plot_type in seaborn_plots:
    try:
        fig = generate_plot_local(df, plot_type=plot_type, x=df.columns[0])
        print(f"✅ {plot_type}: Success")
    except Exception as e:
        print(f"❌ {plot_type}: {str(e)}")

# Test 3: Advanced Preprocessing
print("\n" + "=" * 60)
print("TEST 3: Advanced Preprocessing")
print("=" * 60)

# Test SMOTE (need a classification target)
df_test = df.copy()
df_test['target'] = (df_test.iloc[:, 0] > df_test.iloc[:, 0].median()).astype(int)

preprocessing_tests = [
    {"missing": "iterative", "name": "Iterative Imputation"},
    {"outlier": "isolation", "name": "Isolation Forest"},
    {"scaling": "robust", "name": "Robust Scaling"},
    {"encode": "frequency", "name": "Frequency Encoding"},
    {"reduce_dims": True, "red_method": "lda", "target_column": "target", "name": "LDA"},
    {"polynomial_features": True, "poly_degree": 2, "name": "Polynomial Features"},
    {"handle_imbalance": True, "target_column": "target", "name": "SMOTE"},
]

for test in preprocessing_tests:
    try:
        name = test.pop('name')
        result = preprocess_dataset(df_test.copy(), **test)
        print(f"✅ {name}: {result.shape}")
    except Exception as e:
        print(f"❌ {name}: {str(e)}")

# Test 4: 3D and Hierarchical Plots
print("\n" + "=" * 60)
print("TEST 4: 3D and Hierarchical Plots")
print("=" * 60)

advanced_plots = [
    ('scatter_3d', {'x': df.columns[0], 'y': df.columns[1], 'z': df.columns[2]}),
    ('surface', {'x': df.columns[0], 'y': df.columns[1], 'z': df.columns[2]}),
    ('sunburst', {'names': 'species' if 'species' in df.columns else df.columns[-1], 'values': df.columns[0]}),
]

for plot_type, kwargs in advanced_plots:
    try:
        fig = generate_plot_local(df, plot_type=plot_type, **kwargs)
        print(f"✅ {plot_type}: Success")
    except Exception as e:
        print(f"⚠️ {plot_type}: {str(e)}")

print("\n" + "=" * 60)
print("🎉 ALL TESTS COMPLETED!")
print("=" * 60)
