import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



# Function to compute the empirical CDF
def compute_empirical_cdf(data):
    data_sorted = np.sort(data)
    empirical_cdf_values = np.arange(1, len(data) + 1) / len(data)
    return data_sorted, empirical_cdf_values


# Define the theoretical CDF for the exponential distribution
def exp_cdf(x, lambda_):
    return 1 - np.exp(-lambda_ * x)


# Function for the Kolmogorov-Smirnov test
def ks_test(data, theoretical_cdf, *params):
    data_sorted, empirical_cdf_values = compute_empirical_cdf(data)
    theoretical_cdf_values = theoretical_cdf(data_sorted, *params)
    d_statistic = np.max(np.abs(empirical_cdf_values - theoretical_cdf_values))
    return d_statistic, data_sorted, empirical_cdf_values, theoretical_cdf_values


# קריאת קובץ האקסל

df = pd.read_excel('C:/Users/yuval/Documents/project-simultsia/Check_INOUT_Samples_Minutes.xlsx')


# בחירת עמודות לניתוח
columns_to_analyze = ['CheckIN', 'CheckOut']

# משתנה לשמירת תוצאות
results = {}

# ניתוח כל עמודה
for column in columns_to_analyze:
    # הסרת ערכים חסרים והמרה לפורמט מספרי
    data = df[column].dropna().astype(float)

    # MLE לחישוב lambda
    lambda_mle = 1 / np.mean(data)

    # ביצוע בדיקת KS
    d_statistic, data_sorted, empirical_cdf_values, theoretical_cdf_values = ks_test(data, exp_cdf, lambda_mle)

    # חישוב ערך p (אומדן גס)
    n = len(data)
    p_value = np.exp(-2 * (d_statistic ** 2) * n)

    # שמירת התוצאות
    results[column] = {
        'data_sorted': data_sorted,
        'empirical_cdf_values': empirical_cdf_values,
        'theoretical_cdf_values': theoretical_cdf_values,
        'd_statistic': d_statistic,
        'p_value': p_value,
        'lambda_mle': lambda_mle
    }

    # הדפסת התוצאות
    print(f"Results for {column}:")
    print(f"  KS Statistic: {d_statistic}")
    print(f"  P-value: {p_value}")
    if p_value > 0.05:
        print("  Fail to reject the null hypothesis (H0). The data follows the exponential distribution.")
    else:
        print("  Reject the null hypothesis (H0). The data does not follow the exponential distribution.")
    print()

# ויזואליזציה
plt.figure(figsize=(10, 7))
for column, res in results.items():
    plt.step(res['data_sorted'], res['empirical_cdf_values'], where='post', label=f"Empirical CDF ({column})")
    plt.plot(res['data_sorted'], res['theoretical_cdf_values'], linestyle='--', label=f"Theoretical CDF ({column})")

plt.title("Empirical vs. Theoretical CDFs")
plt.xlabel("Data")
plt.ylabel("CDF")
plt.legend()
plt.grid()
plt.show()

#find mle

# Perform MLE using minimize from scipy.optimize


result = minimize(neg_log_likelihood, initial_guess, args=(data,), bounds=[(0.0001, None)])
lambda_mle = result.x[0]
# Perform KS test using scipy
d_statistic, p_value = kstest(data, 'expon', args=(0, 1/lambda_mle))