# Chapter 9: Efficient Investment Portfolios: An Application of the ZCAPM

**Authors:** J. W. Kolari, M. Liu, and J. Huang  
**Book:** *A New Model of Capital Asset Prices*  
**Publisher:** Springer Nature Switzerland AG (2021)  
**DOI:** [10.1007/978-3-030-65197-8_9](https://doi.org/10.1007/978-3-030-65197-8_9)  
**Pages:** Book pp. 225–255 (PDF pp. 246–276)

---

## Abstract

This chapter constructs aggregate stock market portfolios that outperform general market indexes in out-of-sample tests. Given that most mutual funds cannot consistently outperform general market indexes over time, the performance of our aggregate portfolios is impressive. To achieve these results, we apply the ZCAPM to develop weights for individual stocks in well-diversified portfolios. The analyses employ U.S. stock returns from 1965 to 2018. As in previous chapters, we estimate the empirical ZCAPM using one year of daily returns. Zeta risk coefficient estimates from the ZCAPM are employed to create 24 stock portfolios with different zeta risk levels. One-month-ahead (out-of-sample) returns are computed for these portfolios. Next, the 24 portfolios are formed into 12 long/short portfolios with increasing levels of zeta risk. These portfolios’ average returns are shown to increase linearly with both zeta risk and total risk. Lastly, we add the long/short zeta risk portfolios to the CRSP index to form aggregate portfolios with different total risk levels. Average one-month-ahead returns in our sample period and their standard deviation of returns are plotted to trace out the shape of a mean-variance parabola. Further analyses utilize the empirical ZCAPM to estimate a proxy for the minimum variance portfolio (denoted $g$). When this portfolio is added to the long/short zeta risk portfolios, a more efficient frontier is obtained with higher returns per unit total risk than when using the CRSP index. Additionally, long only aggregate portfolios are formed using either the CRSP index or portfolio $g$ in combination with long zeta risk portfolios. In general, our results show that superior aggregate portfolios with higher Sharpe ratios than the CRSP value-weighted index can be constructed based on both long/short and long only zeta risk portfolios.

**Keywords:** Aggregate portfolios · Asset pricing · Beta risk · CRSP index · Efficient portfolios · Investment technology · Mean-variance parabola · Minimum variance portfolio · Momentum · Multifactor models · Return dispersion · Sharpe ratio · ZCAPM · Zero-beta CAPM · Zeta risk

---

## 9.1 Preview of Portfolio Results

According to our previous mean-variance parabola findings in Chapters 3 and 4, the average market return lies approximately on the axis of symmetry in the middle of the parabola, and the width of the parabola is substantially shaped by return dispersion (RD). These new insights about the investment parabola are relevant to the ZCAPM, wherein average market returns and RD are return generating factors that explain asset returns. The geometry of the ZCAPM uses these two factors to specify a special case of Black’s zero-beta CAPM based on efficient and inefficient (zero-beta) minimum variance portfolios. The ZCAPM approximates these portfolios by moving horizontally along the axis of symmetry of the parabola at the average market return and then vertically up or down within the parabola using zeta risk related to RD to locate portfolios $I^*$ and $ZI^*$ (see Chapter 3). Can this geometry be used to create efficient portfolios with relatively high returns per unit risk compared to general market indexes? In this section we preview our findings, which show that high performing portfolios can be created using the geometry of the ZCAPM.

We begin by estimating the empirical ZCAPM with one year of daily returns in 1964 for individual stocks in the U.S. stock market. Stocks are formed into 24 portfolios based on their ranked zeta coefficient estimates. Then 12 long/short portfolios are created that have different levels of zeta risk. Average stock returns in the next month (out-of-sample) of January 1965 are computed for these portfolios. This procedure is repeated month-by-month to obtain a time series of monthly returns for these portfolios from January 1965 to December 2018. Upon doing so, we find a strong linear relationship between these portfolios’ returns and both zeta risk and total risk.

Next, to construct aggregate portfolios with different risk levels, we combine the CRSP index with each of the 12 long/short zeta risk portfolios. These aggregate portfolios are shown to trace out an upward sloping frontier in mean-variance space that has higher returns than the CRSP index. Moreover, because they have higher average returns per unit total risk than the CRSP index, the Sharpe ratios of the aggregate portfolios are up to three times higher than the CRSP index. We also substitute an empirical proxy for the minimum variance portfolio (denoted $g$) for the CRSP index to construct aggregate portfolios with long/short zeta risk portfolios. The resulting efficient frontier dominates that using the CRSP index and earns up to about four times higher Sharpe ratios than the CRSP index.

One problem with the above approach to constructing aggregate portfolios is that short positions are included in the long/short zeta risk portfolios. Many institutional investors (such as pension funds, mutual funds, etc.) are restricted to long only portfolios. Consequently, we repeat the above procedures by combining the CRSP index with the 24 long only zeta risk portfolios (i.e., short positions are omitted). While less efficient than aggregate portfolios with long/short positions, these long only aggregate portfolios still trace out an efficient frontier that outperforms the CRSP index. In particular, we find that Sharpe ratios for these long only aggregate portfolios are up to 50% higher than the CRSP index. Further results are produced that create long only aggregate portfolios combining either the CRSP index or our minimum variance portfolio proxy $g$ with 24 long only zeta risk portfolios. Again the aggregate portfolios trace out an efficient frontier that outperforms the CRSP index.

Our empirical results have direct implications to the global asset management industry. For over 50 years active investment fund managers have attempted to outperform general market indexes. Academic studies dating back to the late 1960s have consistently documented that active mutual funds underperform general market indexes (e.g., Jensen 1968; Malkiel 1995, 2005; Bollen and Busse 2004; Fama and French 2010; Barras et al. 2010). The failure of active managers to outperform general market indexes is a cornerstone of the efficient market hypothesis (EMH) proposed by Fama (1970). However, the EMH assumes that the market portfolio is efficient. If general market proxies like the CRSP index are inefficient, as shown by our results, the underperformance of active mutual funds could be due to tracking an inefficient market index. Our findings indicate that it is possible to construct aggregate portfolios that are more efficient than general market indexes without taking on excess risk. Indeed, we show that aggregate portfolios can be constructed that have both higher average returns and lower risk than the CRSP index.

---

## 9.2 Background Discussion

To our knowledge, no previous studies apply an asset pricing model to create aggregate stock market portfolios that outperform general market indexes. In this section we discuss previous literature on portfolio construction and explain why the ZCAPM is suitable for constructing superior aggregate portfolios.

Asset pricing models attempt to explain the cross-section of expected stock returns. According to the CAPM of Sharpe (1964), expected stock returns are a positive, linear function of market beta. However, empirical tests of the CAPM have repeatedly failed to find a positive relation between market beta and average stock returns (e.g., Fama and French 1992, 2004). In response, researchers have proposed multifactor models that add size, value, momentum, and other factors to the CAPM (e.g., Fama and French 1993, 2015; Carhart 1997). While these multifactor models have improved explanatory power in-sample, their factor premiums are ad hoc in nature and lack economic justification. More importantly, factors in multifactor models are constructed from firm characteristics rather than derived from an equilibrium asset pricing model. Consequently, multifactor models cannot provide guidance on how to construct efficient portfolios that outperform general market indexes.

By contrast, the ZCAPM is an equilibrium asset pricing model derived from expected utility maximization in a mean-variance framework. In the ZCAPM, asset returns are generated by average market returns and cross-sectional return dispersion (RD). Return dispersion measures the degree of cross-sectional variance of asset returns at time $t$. Assets with positive (negative) sensitivity to RD should earn higher (lower) returns than the overall stock market. By forming portfolios with different zeta risk levels, portfolios with different risk/return profiles can be constructed. We next review the ZCAPM for ease of reference in the next section on building portfolios based on zeta risk.

As mathematically derived in Chapter 3, the theoretical ZCAPM is a special case of Black (1972) zero-beta CAPM. According to the ZCAPM, the expected return for the $i$th asset at time $t$ is[^1]:

$$E(R_{it}) - R_{ft} = \beta_{i,a}[E(R_{at}) - R_{ft}] + Z^*_{i,a}\sigma_{at}, \tag{9.1}$$

where $E(R_{at})$ is the expected market return based on the average return of all assets (rather than a proxy $m$ for the theoretical market portfolio $M$ in Sharpe [1964] CAPM), $R_{ft}$ is the riskless rate, $\beta_{i,a}$ is the beta risk coefficient measuring sensitivity to expected excess market returns, $\sigma_{at}$ is the cross-sectional standard deviation of all asset returns (or return dispersion denoted RD) at time $t$, and $Z^*_{i,a}$ is the zeta risk coefficient measuring dichotomous positive or negative sensitivity to return dispersion. The asterisk on $Z^*_{i,a}$ links zeta risk to theoretical orthogonal portfolios $I^*$ and $ZI^*$ on the mean-variance investment parabola. These efficient and zero-beta portfolios, respectively, are unique due to their equal return variances.

As proposed in Chapter 4, to estimate the ZCAPM, the following novel empirical ZCAPM is employed[^2]:

$$R_{it} - R_{ft} = \beta_{i,a}(R_{at} - R_{ft}) + Z_{i,a} D_{it} \sigma_{at} + u_{it}, \quad t = 1, \dots, T \tag{9.2}$$

where $R_{it} - R_{ft}$ is the excess return for the $i$th stock portfolio (or stock) over the Treasury bill rate, $\beta_{i,a}$ measures sensitivity of the $i$th stock portfolio (or stock) to excess average market returns based on the value-weighted CRSP index minus Treasury bill rate equal to $R_{at} - R_{ft}$, $Z_{i,a}$ measures sensitivity of the $i$th stock portfolio (or stock) to return dispersion $\sigma_{at}$ (denoted RD), $D_{it}$ is a signal variable with values $+1$ and $-1$ representing positive and negative RD effects, respectively, on stock returns, and $u_{it} \sim \text{i.i.d. } N(0, \sigma_i^2)$.[^3] Importantly, signal variable $D_{it}$ is defined as an independent random variable with the following two-point distribution:

$$D_{it} = \begin{cases} +1 & \text{with probability } p_i \\ -1 & \text{with probability } 1 - p_i \end{cases} \tag{9.3}$$

We use the expectation–maximization (EM) algorithm (see Dempster et al. 1977) to estimate the parameters of the empirical ZCAPM including the probability parameter $p_i$.[^4] Since $E(D_{it}) = 2p_i - 1$, the marginal form of the empirical ZCAPM is:

$$R_{it} - R_{ft} = \beta_{i,a}(R_{at} - R_{ft}) + Z^*_{i,a}\sigma_{at} + u^*_{it}, \quad t = 1, \dots, T \tag{9.4}$$

where $\beta_{i,a}$ is the beta risk coefficient, $Z^*_{i,a} = Z_{i,a}(2p_i - 1)$ is the zeta risk coefficient, $u^*_{it}$ is the error term with variance related to return dispersion (see Eq. (4.13) of Chapter 4), and other notation is as before. Whether the sign of zeta risk loading $Z^*_{i,a}$ is positive or negative is determined by the probability $p_i$ associated with the expected value of signal variable $D_{it}$ in period $t = 1, \dots, T$.

Matlab programs for estimating the empirical ZCAPM are available at the end of the book in the Compendium. Additionally, R programs for these analyses can be downloaded from GitHub ([https://github.com/zcapm](https://github.com/zcapm)). R is a free software environment available on the internet. Our R programs run faster than the Matlab programs.

---

## 9.3 Building Portfolios Based on Zeta Risk

We use all U.S. stocks in the intersection of the NYSE, AMEX, and NASDAQ return files from the Center for Research in Security Prices (CRSP) in the period January 1964 to December 2018. Relatively small firms with market capitalization in the bottom 10% at year-end are dropped in the next year. Daily CRSP value-weighted returns and Treasury bill rates are used to proxy mean market returns ($R_{at}$) and riskless returns ($R_{ft}$), respectively. To proxy the cross-sectional standard deviation of assets’ returns (i.e., RD), value-weighted returns for $i = 1, \dots, n$ assets on day $t$ ($R_{it}$) are used to compute

$$\sigma_{at} = \sqrt{\frac{n}{n - 1} \sum_{i=1}^n w_{it-1}(R_{it} - R_{at})^2}, \tag{9.5}$$

where $w_{it} =$ the market value weight for asset $i$. Within our analysis period January 1965 to December 2018, the mean daily RD of stocks in the CRSP index equals 1.81%, and the mean daily CRSP return is 0.04%. Hence, cross-sectional market RD is large in magnitude relative to mean market returns on any given day $t$. Relevant to later evaluating the performance of aggregate portfolios constructed using the empirical ZCAPM, the mean monthly CRSP return and standard deviation of CRSP monthly returns throughout our analysis period equal 0.88% and 4.44%, respectively (see Table 5.1 in Chapter 5).

We begin by utilizing the sensitivity of stocks to RD movements (i.e., zeta risk) to construct zero-investment portfolios.[^5] The following steps are used to build a variety of zero-investment (long/short) stock portfolios with different zeta risk levels:

1. Time-series regressions are used to estimate empirical ZCAPM Eq. (9.4) via the expectation–maximization (EM) algorithm for all individual stocks with daily returns for the initial 12-month estimation period January to December 1964.
2. All stocks are ranked in terms of their estimated zeta coefficient $\hat{Z}^*_{i,a}$.
3. A total of 24 portfolios are formed from positive to negative zeta risk. Equal-weighted returns are computed for each portfolio in the next month January 1965 (i.e., out-of-sample returns).
4. Using these portfolios, 12 zero-investment portfolios are formed with one long and one short portfolio:
   - **(a)** Portfolios 1 and 2 are zero-investment portfolios that are long/short in stocks with high zeta market risk $\hat{Z}^*_{i,a}$ in the top $+1\%/\text{bottom } -1\%$ and top $+2\%/\text{bottom } -2\%$ of all sample stocks, respectively. We form these tail portfolios to better understand extreme risk/return profiles associated with RD.
   - **(b)** Portfolios 3 to 12 are comprised of long/short stocks in incremental $+5/-5\%$ portfolios with respect to zeta risk $\hat{Z}^*_{i,a}$. More specifically, portfolio 3 contains the top $+5/-5\%$ stocks with relatively high zeta risk coefficients, portfolio 4 contains the next $+5/-5\%$ of stocks per their zeta risk coefficients, ..., portfolio 12 contains the bottom $+5/-5\%$ stocks with zeta risk coefficients near zero.
5. For all stocks in each long/short zeta risk portfolio, we compute the one-month-ahead (out-of-sample), equal-weighted portfolio holding period return $R_{pt+1}$ in January 1965.[^6] This out-of-sample approach mimics actual investor behavior in terms of forming portfolios at time $t = T$ and then observing their performance in the next month $T + 1$.
6. The above process is repeated by rolling the estimation period in step (1) forward one month at a time to rebalance the zero-investment, return dispersion portfolios until their last one-month-ahead holding period returns are computed in December 2018. The time-series standard deviation of these 648 out-of-sample portfolio returns in the analysis period January 1965 to December 2018 is computed also.

Our 12 zero-investment portfolios based on zeta risk span a wide range of market risk associated with cross-sectional RD. If there is a relation between one-month-ahead returns and zeta risk loadings, average returns should increase from low for portfolio 12 to high for portfolio 1.

We build aggregate zeta risk portfolios by combining the value-weighted CRSP index with each of the 12 zero-investment, zeta risk portfolios. Aggregate portfolios have weights for all CRSP stocks that add to one plus a positive weight for the long/short zeta risk portfolios. Post-formation, one-month-ahead returns are computed for these aggregate zeta risk portfolios from January 1965 to December 2018. As an example to clarify our assumptions, suppose that you have $100 dollars and buy the CRSP index that earns the average market return. At the same time, your brokerage firm allows you to buy $100 stocks (long) and sell $100 stocks (short) in a long/short portfolio (i.e., a positive constant 1 is assigned as the weight for the long/short zeta risk portfolio). After one month, the CRSP index generates $2 and the long/short portfolio earns $3, such that your total return is $(\\$2 + \\$3)/\\$100 = 5\%$. This aggregate portfolio is leveraged.[^7]

Previous studies have shown that short positions are needed to create more efficient portfolios.[^8] However, a criticism of this approach is that many investors only hold long portfolios (e.g., pension funds, mutual funds, etc.). Accordingly, we also examine the average performance of the 24 zeta risk portfolios with long only positions. Moreover, we build 24 long only aggregate portfolios by investing 50% of funds in the CRSP index and 50% in each long zeta risk portfolio, which enables insights into the effects of restricting aggregate portfolios to long only positions compared to allowing short positions.

Lastly, we build another set of aggregate portfolios based on a proxy for the theoretical minimum variance portfolio $G$ denoted $g$. As discussed in Chapter 3, the CRSP index lies on the axis of symmetry of the mean-variance parabola and therefore is not an efficient portfolio. A more efficient general market index is the portfolio $G$ located at the vertex of the parabola. To develop a proxy $g$ portfolio from the empirical ZCAPM, we reduce both idiosyncratic and zeta risks (i.e., $g$ has little or no zeta risk as it is unaffected by return dispersion that defines the width of the investment parabola per our findings in Chapters 3 and 4). As in the case of the zeta risk portfolios, we drop the lowest 10% of stocks by market capitalization at year-end in the subsequent year. Also, we drop stocks with standard deviations of monthly returns in each one-year estimation period less than 20% of the CRSP index. This volatility filter eliminates stocks in each estimation window with volatility less than a highly diversified market index. These stocks are likely very illiquid or have other issues that are idiosyncratic (i.e., firm specific) in nature. To build portfolio $g$, we follow steps similar to the construction of the 24 zeta risk portfolios:

1. Time-series regressions are used to estimate the empirical ZCAPM Eq. (9.4) via the expectation–maximization (EM) algorithm for all individual stocks with daily returns for the initial 12-month estimation period January to December 1964.
2. To reduce idiosyncratic and zeta risks, all stocks are weighted as:
   $$w_i = \frac{1}{0.01 + |\hat{Z}^*_{i,a}|} \times \frac{1}{\operatorname{var}(u_{it})}$$
   where idiosyncratic risk is measured by the variance of the residual error terms denoted $\operatorname{var}(u_{it})$, and 0.01 is added to the absolute value of the estimated zeta risk coefficient $\hat{Z}^*_{i,a}$ to avoid the case of singularity when $\hat{Z}^*_{i,a} = 0$.[^9]
3. For all stocks, we compute the one-month-ahead, weighted portfolio holding period return $R_{gt+1}$ in January 1965.
4. The above process is repeated by rolling the estimation period in step (1) forward one month at a time to rebalance portfolio $g$ until the last one-month-ahead holding period return is computed in December 2018.

As in the case of the CRSP index, aggregate portfolios are formed by combining proxy minimum variance portfolio $g$ with the 12 long/short zeta risk portfolios.

---

## 9.4 Empirical Results

### 9.4.1 Zero-Investment Portfolios Sensitive to Return Dispersion

The average return and risk results for the 12 zero-investment, return dispersion portfolios created from 24 zeta risk portfolios are shown in Table 9.1. As discussed in the previous section, zeta risk coefficients $Z^*_{i,a}$ for individual stocks are estimated using a one-year period with daily returns. Stocks are sorted into 24 zeta risk portfolios which are used to construct 12 long/short portfolios. For each long, short, and long/short portfolio in the analysis period January 1965 to December 2018, the table reports the average estimated zeta risk coefficient for constituent stocks denoted $\bar{Z}^*_{pt}$ (i.e., 12-month zeta risk estimates are rolled forward one month at a time to yield 648 estimates for each portfolio ending in November 2018), their average one-month-ahead return denoted $\bar{R}_{pt+1}$ (for 648 months from January 1965 to December 2018), and the time-series standard deviation of these estimates in parentheses. Strikingly, for stocks in portfolios 1, 2, and 3 containing the top $+1\%/\text{bottom } -1\%$, top $+2\%/\text{bottom } -2\%$, and top $+5\%/\text{bottom } -5\%$ slices of estimated zeta risk coefficients, average returns in the post-formation month are $2.34\%$, $2.16\%$, and $1.96\%$ per month, respectively. These returns are exceptional given that the long/short portfolios are market neutral and zero-investment.[^10]

#### Table 9.1: Construction details for long/short zeta risk portfolios

| Zero-investment portfolios | Long $\bar{Z}^*_{pt}$ | Short $\bar{Z}^*_{pt}$ | Long $-$ Short $\bar{Z}^*_{pt}$ | Long $\bar{R}_{pt+1}$ (%) | Short $\bar{R}_{pt+1}$ (%) | Long $-$ Short $\bar{R}_{pt+1}$ (%) | Sharpe ratio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Portfolio 1 – Top +1% / −1%** | 5.75<br>(1.64) | −4.99<br>(1.28) | 10.73<br>(1.66) | 1.86<br>(9.19) | −0.48<br>(11.06) | 2.34<br>(9.12) | 0.26 |
| **Portfolio 2 – Top +2% / −2%** | 5.15<br>(1.47) | −4.54<br>(1.17) | 9.68<br>(1.42) | 1.77<br>(7.56) | −0.39<br>(10.30) | 2.16<br>(7.67) | 0.28 |
| **Portfolio 3 – Top +5% / −5%** | 4.17<br>(1.21) | −3.74<br>(0.99) | 7.91<br>(1.06) | 1.80<br>(7.84) | −0.16<br>(9.15) | 1.96<br>(6.78) | 0.29 |
| **Portfolio 4** | 2.53<br>(0.80) | −2.30<br>(0.71) | 4.82<br>(0.59) | 1.69<br>(6.49) | 0.41<br>(7.38) | 1.29<br>(4.98) | 0.26 |
| **Portfolio 5** | 1.87<br>(0.66) | −1.65<br>(0.61) | 3.52<br>(0.46) | 1.56<br>(5.84) | 0.51<br>(6.52) | 1.04<br>(3.92) | 0.27 |
| **Portfolio 6** | 1.45<br>(0.58) | −1.23<br>(0.55) | 2.68<br>(0.38) | 1.47<br>(5.36) | 0.72<br>(5.96) | 0.75<br>(3.35) | 0.22 |
| **Portfolio 7** | 1.13<br>(0.52) | −0.91<br>(0.50) | 2.05<br>(0.32) | 1.31<br>(5.10) | 0.79<br>(5.61) | 0.52<br>(2.72) | 0.19 |
| **Portfolio 8** | 0.88<br>(0.48) | −0.66<br>(0.46) | 1.54<br>(0.27) | 1.24<br>(4.84) | 0.81<br>(5.29) | 0.43<br>(2.18) | 0.20 |
| **Portfolio 9** | 0.66<br>(0.45) | −0.46<br>(0.43) | 1.12<br>(0.23) | 1.12<br>(4.76) | 0.88<br>(5.02) | 0.24<br>(1.80) | 0.13 |
| **Portfolio 10** | 0.48<br>(0.42) | −0.28<br>(0.40) | 0.76<br>(0.18) | 1.11<br>(4.64) | 0.96<br>(4.82) | 0.15<br>(1.54) | 0.10 |
| **Portfolio 11** | 0.31<br>(0.40) | −0.13<br>(0.38) | 0.44<br>(0.12) | 1.07<br>(4.58) | 0.94<br>(4.73) | 0.13<br>(1.22) | 0.11 |
| **Portfolio 12 – Bottom +5% / −5%** | 0.16<br>(0.38) | 0.02<br>(0.37) | 0.14<br>(0.05) | 1.00<br>(4.59) | 0.93<br>(4.68) | 0.07<br>(1.05) | 0.07 |
| **CRSP index $- R_f$** | — | — | — | — | — | 0.50<br>(4.44) | 0.11 |
| **Portfolio $g - R_f$** | — | — | — | — | — | 0.57<br>(3.50) | 0.16 |

*Notes:* This table reports construction details for zero-investment, return dispersion (RD) portfolios. Individual stocks are sorted in the estimation period based on their estimated $Z^*_{i,a}$ coefficients in the empirical ZCAPM. Long/short portfolios are formed using stocks with high/low $Z^*_{i,a}$ coefficients. Average one-month-ahead portfolio returns in the analysis period January 1965 to December 2018 are shown (with time-series standard deviations in parentheses). Average $Z^*_{i,a}$ coefficients for portfolios are shown also. We report Sharpe ratios as well as descriptive statistics for long/short portfolios. For comparison purposes, information is shown for excess returns of the CRSP index minus Treasury bills ($R_f$) and the proxy minimum variance portfolio $g$ (developed from the empirical ZCAPM) minus Treasury bills.

---

As shown in Table 9.1, for stocks in zero-investment portfolios 1–12, average one-month-ahead returns $\bar{R}_{pt+1}$ consistently decline from 2.34% to 0.07% per month. Average monthly returns for long portfolios 1–12 decline from 1.86% to 1.00% per month, and short portfolios’ returns increase from $-0.48\%$ to $0.93\%$ per month. These patterns strongly support the ability of estimated zeta risk coefficients to stratify one-month-ahead stock returns in out-of-sample tests. Notice that the long portfolios earn positive returns in all cases, while the short portfolios 1, 2, and 3 with high negative zeta risk earn negative average returns. Sharpe ratios for the 12 zero-investment portfolios range from 0.07 for portfolio 12 to 0.29 for portfolio 3, with portfolios 1–5 having Sharpe ratios between 0.26 and 0.29. By comparison, the Sharpe ratio for the CRSP excess return ($CRSP - R_f$) is 0.11, and that for the minimum variance portfolio proxy ($g - R_f$) is 0.16.

Turning to the construction details of the zero-investment portfolios in Table 9.1, the average estimated zeta risk coefficients $\bar{Z}^*_{pt}$ for long and short stocks in portfolios 1–12 range from 5.75 to 0.16 and $-4.99$ to 0.02, respectively. For long/short portfolios, the difference $\bar{Z}^*_{pt}(\text{long}) - \bar{Z}^*_{pt}(\text{short})$ ranges from 10.73 for portfolio 1 to 0.14 for portfolio 12. Notice that the standard deviation of monthly returns in parentheses are higher at 9.19% and 7.56% compared to 4.44% for the CRSP index.

Using results in Table 9.1, Fig. 9.1 graphs the relationship between average one-month-ahead returns and average zeta risk coefficients, $\bar{Z}^*_{pt}$, for the 12 zero-investment long/short portfolios based on zeta risk. Further supporting the ZCAPM, a strong positive and linear relationship exists between average one-month-ahead returns and estimated zeta risk.

![Fig. 9.1](images/fig9_1.jpg)  
*Fig. 9.1: A positive, linear relation is shown between average one-month-ahead (out-of-sample) returns for 12 long/short zeta risk portfolios formed based on zeta coefficient estimates in the previous year. The analysis period is January 1965 to December 2018.*

Average one-month-ahead returns for the 12 zero-investment portfolios with respect to their time-series standard deviation of returns are plotted in Fig. 9.2. A striking positive, linear relation between average returns and total risk is evident. At the low risk end, portfolio 12 has a standard deviation of 1.05% and average return of 0.07% per month. As zeta risk increases, both risk and return increase monotonically to portfolio 1 with a standard deviation of 9.12% and average return of 2.34% per month. For comparison purposes, Fig. 9.2 plots the CRSP index as well as popular multifactor long/short portfolios: size ($SMB$), value ($HML$), profitability ($RMW$), investment ($CMA$), and momentum ($MOM$) obtained from Kenneth French’s website. Notice that our long/short zeta risk portfolios trace out an efficient linear relationship that spans a wide range of risk and return, whereas the multifactor portfolios plot at isolated, arbitrary locations.

![Fig. 9.2](images/fig9_2.jpg)  
*Fig. 9.2: A positive, linear relation is shown between average one-month-ahead (out-of-sample) returns and the time-series standard deviation of these returns for 12 long/short zeta risk portfolios. Visual comparisons can be made to the CRSP index as well as popular long/short multifactors size ($SMB$), value ($HML$), profit ($RMW$), capital investment ($CMA$), and momentum ($MOM$) from Kenneth French’s website. The analysis period is January 1965 to December 2018.*

It is noteworthy that previous researchers provide little or no explanation for these anomalous multifactor returns. By contrast, the linear relation in Fig. 9.2 is directly predicted by the ZCAPM.

It is important to recognize that the 12 zero-investment portfolios in Fig. 9.2 are financially engineered by progressively adding zeta risk. In practice, an investment manager can control the amount of zeta risk and, in turn, the relative return compared to other portfolios that span different levels of zeta risk. An important advantage of these engineered portfolios based on zeta risk is the ability to control their relative risks and returns over time.

---

### 9.4.2 Aggregate Portfolios Sensitive to Return Dispersion

Here we report the results for aggregate stock portfolios based on combining either the CRSP value-weighted index or the proxy minimum variance portfolio $g$ with each of our 12 zero-investment, long/short zeta risk portfolios. As described earlier, each aggregate portfolio allocates 100% of funds to the market proxy (CRSP or $g$) plus a 100% weight to one of the 12 long/short zeta risk portfolios. Thus, these aggregate portfolios have aggregate weights for all stocks greater than one and therefore are leveraged due to inclusion of short positions in the zero-investment portfolios. One-month-ahead returns are computed for aggregate portfolios from January 1965 to December 2018 (648 months).

Figure 9.3 shows the relationship between average one-month-ahead returns for our 12 aggregate portfolios based on the CRSP index as well as the 12 aggregate portfolios based on proxy minimum variance portfolio $g$ with respect to the time-series standard deviation of these returns. In addition, the CRSP index, portfolio $g$, and aggregate portfolios combining CRSP or $g$ with the five popular Fama–French multifactors ($SMB$, $HML$, $RMW$, $CMA$, and $MOM$) are shown.

![Fig. 9.3](images/fig9_3.jpg)  
*Fig. 9.3: Frontier estimates are shown based on average one-month-ahead (out-of-sample) returns and the time-series standard deviation of these returns for aggregate portfolios with different levels of zeta risk. Aggregate portfolios are constructed by adding either the CRSP market index (denoted a) or the proxy minimum variance portfolio $g$ to 12 long/short zeta risk portfolios. Visual comparisons can be made to the CRSP market index, portfolio $g$, and aggregate portfolios combining either the CRSP index or portfolio $g$ with popular long/short multifactors size ($SMB$), value ($HML$), profit ($RMW$), capital investment ($CMA$), and momentum ($MOM$) from Kenneth French’s website. The analysis period is January 1965 to December 2015.*

Using the CRSP index in combination with 12 long/short zeta risk portfolios, and assuming leveraged positions, average monthly returns increase from 0.95% for CRSP + portfolio 12 to 3.22% for CRSP + portfolio 1. As shown in Fig. 9.3, the 12 aggregate portfolios trace out an upward sloping, slightly curved frontier in mean-variance space that clearly outperforms the CRSP index. For all 12 aggregate portfolios, average monthly returns exceed the CRSP index (0.88%).

Turning to aggregate portfolios created by combining proxy minimum variance portfolio $g$ with the 12 long/short zeta risk portfolios, an even more efficient frontier is established. As seen in Fig. 9.3, the frontier for $g$ plus zeta risk portfolios lies above and to the left of the frontier based on the CRSP index. Average monthly returns range from 1.03% for $g$ + portfolio 12 to 3.30% for $g$ + portfolio 1, with lower standard deviations than the corresponding CRSP aggregate portfolios across all zeta risk levels.

The empirical evidence for aggregate portfolios formed by combining the CRSP index or proxy minimum variance portfolio $g$ with long/short zeta risk portfolios supports our new geometric findings in Chapters 3 and 4 concerning the mean-variance investment parabola. There we proposed that the average return of all assets in the market lies approximately on the axis of symmetry at an interior location and cross-sectional return dispersion defines the span of the parabola. Relevant to the former proposition, using the frontier traced out by the 12 aggregate portfolios incorporating portfolio $g$ in Fig. 9.3, the CRSP index lies at an interior position along the axis of symmetry as previously conjectured. Thus, our out-of-sample aggregate portfolios corroborate earlier insights about the shape of the investment parabola.

#### Table 9.2: Construction details for aggregate portfolios composed of the CRSP index plus long/short zeta risk portfolios

| Aggregate portfolios | $\bar{R}_{CRSPt+1} + \bar{R}_{pt+1}$ (%) | $\sigma_{CRSP+p,t+1}$ (%) | Sharpe ratio |
| :--- | :---: | :---: | :---: |
| **CRSP + portfolio 1** | 3.22 | 9.76 | 0.29 |
| **CRSP + portfolio 2** | 3.04 | 8.12 | 0.33 |
| **CRSP + portfolio 3** | 2.84 | 7.69 | 0.32 |
| **CRSP + portfolio 4** | 2.17 | 6.28 | 0.28 |
| **CRSP + portfolio 5** | 1.93 | 5.56 | 0.28 |
| **CRSP + portfolio 6** | 1.63 | 5.29 | 0.24 |
| **CRSP + portfolio 7** | 1.40 | 4.99 | 0.20 |
| **CRSP + portfolio 8** | 1.31 | 4.74 | 0.20 |
| **CRSP + portfolio 9** | 1.13 | 4.67 | 0.16 |
| **CRSP + portfolio 10** | 1.04 | 4.66 | 0.14 |
| **CRSP + portfolio 11** | 1.02 | 4.56 | 0.14 |
| **CRSP + portfolio 12** | 0.95 | 4.51 | 0.13 |
| **CRSP + SMB** | 1.10 | 6.10 | 0.12 |
| **CRSP + HML** | 1.20 | 4.60 | 0.18 |
| **CRSP + RMW** | 1.15 | 4.46 | 0.17 |
| **CRSP + CMA** | 1.17 | 4.10 | 0.19 |
| **CRSP + MOM** | 1.55 | 5.72 | 0.20 |
| **CRSP index** | 0.88 | 4.44 | 0.11 |

*Notes:* This table reports construction details for aggregate portfolios formed by combining the CRSP index with 12 zero-investment, return dispersion (RD) portfolios formed on slices of zeta risk associated with cross-sectional RD in the empirical ZCAPM. Individual stocks are sorted in the one-year estimation period based on their estimated $Z^*_{i,a}$ coefficients. Long/short portfolios are formed using stocks in the top $+1\%/\text{bottom } -1\%$ and top $+2\%/\text{bottom } -2\%$ of estimated $Z^*_{i,a}$ coefficients (i.e., portfolios 1 and 2, respectively), in addition to 10 zero-investment portfolios based on stocks in progressive $+5/-5\%$ slices of estimated $Z^*_{i,a}$ coefficients (i.e., portfolios 3 to 12). Using 648 months in the analysis period January 1965 to December 2018, we report for each aggregate portfolio the average one-month-ahead return denoted as $\bar{R}_{CRSPt+1} + \bar{R}_{pt+1}$, time-series standard deviation of this aggregate monthly return series denoted as $\sigma_{CRSP+p,t+1}$, and Sharpe ratio. For comparison purposes, results for the CRSP index are shown as well as combinations of the CRSP index with zero-investment multifactors size ($SMB$), value ($HML$), profit ($RMW$), capital investment ($CMA$), and momentum ($MOM$) from Kenneth French’s website.

---

#### Table 9.3: Construction details for aggregate portfolios composed of the proxy minimum variance portfolio $g$ plus long/short zeta risk portfolios

| Aggregate portfolios | $\bar{R}_{gt+1} + \bar{R}_{pt+1}$ (%) | $\sigma_{g+p,t+1}$ (%) | Sharpe ratio |
| :--- | :---: | :---: | :---: |
| **Min var portfolio $g$ + portfolio 1** | 3.30 | 9.19 | 0.32 |
| **Min var portfolio $g$ + portfolio 2** | 3.12 | 7.61 | 0.36 |
| **Min var portfolio $g$ + portfolio 3** | 2.92 | 7.02 | 0.36 |
| **Min var portfolio $g$ + portfolio 4** | 2.25 | 5.51 | 0.34 |
| **Min var portfolio $g$ + portfolio 5** | 2.00 | 4.70 | 0.34 |
| **Min var portfolio $g$ + portfolio 6** | 1.71 | 4.39 | 0.30 |
| **Min var portfolio $g$ + portfolio 7** | 1.48 | 4.04 | 0.27 |
| **Min var portfolio $g$ + portfolio 8** | 1.39 | 3.75 | 0.27 |
| **Min var portfolio $g$ + portfolio 9** | 1.20 | 3.71 | 0.22 |
| **Min var portfolio $g$ + portfolio 10** | 1.11 | 3.67 | 0.20 |
| **Min var portfolio $g$ + portfolio 11** | 1.09 | 3.57 | 0.20 |
| **Min var portfolio $g$ + portfolio 12** | 1.03 | 3.56 | 0.18 |
| **Min var portfolio $g$ + SMB** | 1.18 | 5.63 | 0.14 |
| **Min var portfolio $g$ + HML** | 1.27 | 4.37 | 0.20 |
| **Min var portfolio $g$ + RMW** | 1.22 | 3.78 | 0.22 |
| **Min var portfolio $g$ + CMA** | 1.24 | 3.63 | 0.24 |
| **Min var portfolio $g$ + MOM** | 1.62 | 4.94 | 0.25 |
| **Min var portfolio $g$** | 0.96 | 3.49 | 0.16 |

*Notes:* This table reports construction details for aggregate portfolios formed by combining the proxy minimum variance portfolio $g$ with 12 zero-investment, return-dispersion (RD) portfolios formed on slices of zeta risk associated with cross-sectional RD in the empirical ZCAPM. Portfolio $g$ is developed from the empirical ZCAPM as described in the text. Individual stocks are sorted in the estimation period based on their estimated $Z^*_{i,a}$ coefficients. Long/short portfolios are formed using stocks in the top $+1\%/\text{bottom } -1\%$ and top $+2\%/\text{bottom } -2\%$ of estimated $Z^*_{i,a}$ coefficients (i.e., portfolios 1 and 2, respectively), in addition to 10 zero-investment portfolios based on stocks in progressive $+5/-5\%$ slices of estimated $Z^*_{i,a}$ coefficients (i.e., portfolios 3 to 12). Using 648 months in the analysis period January 1965 to December 2018, we report for each aggregate portfolio the average one-month-ahead return denoted as $\bar{R}_{gt+1} + \bar{R}_{pt+1}$, time-series standard deviation of this aggregate monthly return series denoted as $\sigma_{g+p,t+1}$, and Sharpe ratio. For comparison purposes, results for proxy minimum variance portfolio $g$ are shown as well as combinations of portfolio $g$ with the zero-investment multifactors size ($SMB$), value ($HML$), profit ($RMW$), capital investment ($CMA$), and momentum ($MOM$) from Kenneth French’s website.

---

The Sharpe ratio, defined as the average excess return divided by the standard deviation of returns over time, is commonly used to compare the relative performance of investment portfolios. In terms of this risk-adjusted metric, the results in Tables 9.2 and 9.3 for aggregate portfolios formed using the CRSP index and $g$, respectively, are impressive. For aggregate portfolios based on the CRSP index, Sharpe ratios range from 0.13 to 0.33 compared to the CRSP index itself at 0.11. For aggregate portfolios based on proxy minimum variance portfolio $g$, Sharpe ratios have an even higher range from 0.18 to 0.36 compared to $g$ alone at 0.16. Most aggregate portfolios have Sharpe ratios that are two to three times larger than the CRSP index. For example, CRSP + portfolio 2 has a Sharpe ratio of 0.33, and $g$ + portfolio 2 and $g$ + portfolio 3 have Sharpe ratios of 0.36.

We next apply the well-known Gibbons et al. (1989) test for the efficiency of a portfolio (denoted GRS test). The GRS test evaluates whether the alphas from time-series regressions of excess portfolio returns on excess benchmark returns are jointly zero. When we test the efficiency of the CRSP index against the 12 aggregate portfolios based on the CRSP index, the GRS test statistic is 4.31 ($p$-value $< 0.0001$), which overwhelmingly rejects the hypothesis that the CRSP index is mean-variance efficient. Similarly, testing the efficiency of the CRSP index against the 12 aggregate portfolios based on portfolio $g$ yields a GRS statistic of 4.88 ($p$-value $< 0.0001$). Furthermore, when we include the Fama and French (2018) six factors ($R_m - R_f$, $SMB$, $HML$, $RMW$, $CMA$, and $MOM$) as benchmarks in the GRS test, the test statistic remains highly significant at 3.96 ($p$-value $< 0.0001$) for aggregate portfolios based on the CRSP index and 4.22 ($p$-value $< 0.0001$) for those based on portfolio $g$. Thus, the superior performance of our aggregate portfolios cannot be explained by standard multifactor models.

The outsized performance of our aggregate portfolios is exceptional in view of published literature showing that active mutual funds fail to beat market indexes. Rather than relying on stock picking or market timing, our approach applies an equilibrium asset pricing model to engineer portfolios that exploit cross-sectional return dispersion. Because these portfolios are constructed using an asset pricing model, they reflect compensation for bearing systematic zeta risk under the ZCAPM asset pricing model. Thus, they are consistent with the efficient market hypothesis.

We also report the results of aggregate portfolios combining the CRSP index and portfolio $g$ with popular multifactors from Kenneth French’s website. As shown in Tables 9.2 and 9.3, combining the CRSP index with $SMB$, $HML$, $RMW$, $CMA$, or $MOM$ yields Sharpe ratios between 0.12 and 0.20, which are substantially lower than aggregate portfolios incorporating zeta risk portfolios 1–6 (Sharpe ratios 0.24 to 0.33). Similarly, combining portfolio $g$ with these multifactors yields Sharpe ratios between 0.14 and 0.25, compared to 0.27 to 0.36 for $g$ plus zeta risk portfolios 1–8.

---

### 9.4.3 Long Only Aggregate Portfolios Sensitive to Return Dispersion

The average performances of the 24 long only zeta risk portfolios are displayed in Fig. 9.4. When short positions are not allowed, the 24 long only portfolios trace out an upward sloping relation between return and risk. Portfolios 1–4 with the lowest zeta risk have standard deviations around 8%–11% and average returns of $-0.48\%$ to $0.41\%$ per month. Portfolios 21–24 with the highest zeta risk earn average monthly returns of 1.24% to 1.86% per month with standard deviations around 4.8% to 9.2%.

![Fig. 9.4](images/fig9_4.jpg)  
*Fig. 9.4: Frontier estimates are shown based on average one-month-ahead (out-of-sample) returns and the time-series standard deviation of these returns for 24 long only zeta risk portfolios. Visual comparisons can be made to the CRSP market index and proxy minimum variance portfolio $g$. The analysis period is January 1965 to December 2018.*

When we combine the CRSP index (i.e., 50% weight) with each of these 24 long only zeta risk portfolios (i.e., 50% weight), the resulting long only aggregate portfolios are completely unleveraged and contain no short positions. Figure 9.5 graphs the average one-month-ahead returns and standard deviations for these 24 long only aggregate portfolios.

![Fig. 9.5](images/fig9_5.jpg)  
*Fig. 9.5: Frontier estimates are shown based on average one-month-ahead (out-of-sample) returns and the time-series standard deviation of these returns for 24 long only aggregate portfolios. These long aggregate portfolios are formed by investing 50% of funds in the CRSP market index and 50% of funds in 24 long zeta risk portfolios. Visual comparisons can be made to the CRSP market index and proxy minimum variance portfolio $g$. The analysis period is January 1965 to December 2018.*

Based on combining the CRSP index with the 24 long only zeta risk portfolios, Table 9.4 reports detailed performance statistics. Long only aggregate portfolios formed by combining the CRSP index with long portfolios 10–24 yield Sharpe ratios between 0.12 and 0.17, which exceed the CRSP index at 0.11 (an increase in the range of 35%–45% improvement). Portfolios combining CRSP with portfolios 22, 23, and 24 earn average monthly returns of 1.34%, 1.33%, and 1.37% per month, respectively, which well exceeds the CRSP index at 0.88% per month. Long only aggregate portfolios combining the CRSP index with long portfolios 15 and 16 have similar return volatility as the CRSP index but somewhat higher returns at 1.00% per month.[^11]

Comparing the frontiers based on aggregate portfolios formed with the CRSP index in Figs. 9.3 and 9.5 allows some insight into the effects of short positions on aggregate portfolio efficiency. Consistent with the literature cited earlier, short positions visibly increase efficiency, especially for higher total risk portfolios. As such, our U.S. stock market evidence does not support the CAPM assumption that a positive-by-definition market portfolio is efficient (see Brennan and Lo 2010; Levy and Roll 2010). Short positions enable the formation of more efficient portfolios in the investment opportunity set (see footnote 8 citations).

#### Table 9.4: Construction details for long only aggregate portfolios composed of the CRSP index plus long only zeta risk portfolios

| Long aggregate portfolios | $\bar{R}_{CRSPt+1} + \bar{R}_{pt+1}$ (%) | $\sigma_{CRSP+p,t+1}$ (%) | Sharpe ratio |
| :--- | :---: | :---: | :---: |
| **CRSP + portfolio 1** | 0.20 | 7.24 | −0.03 |
| **CRSP + portfolio 2** | 0.25 | 6.92 | −0.02 |
| **CRSP + portfolio 3** | 0.36 | 6.42 | −0.00 |
| **CRSP + portfolio 4** | 0.64 | 5.63 | 0.05 |
| **CRSP + portfolio 5** | 0.70 | 5.26 | 0.06 |
| **CRSP + portfolio 6** | 0.80 | 4.99 | 0.08 |
| **CRSP + portfolio 7** | 0.84 | 4.83 | 0.09 |
| **CRSP + portfolio 8** | 0.85 | 4.69 | 0.10 |
| **CRSP + portfolio 9** | 0.88 | 4.57 | 0.11 |
| **CRSP + portfolio 10** | 0.92 | 4.47 | 0.12 |
| **CRSP + portfolio 11** | 0.91 | 4.44 | 0.12 |
| **CRSP + portfolio 12** | 0.91 | 4.42 | 0.12 |
| **CRSP + portfolio 13** | 0.94 | 4.39 | 0.13 |
| **CRSP + portfolio 14** | 0.98 | 4.39 | 0.14 |
| **CRSP + portfolio 15** | 1.00 | 4.41 | 0.14 |
| **CRSP + portfolio 16** | 1.00 | 4.47 | 0.14 |
| **CRSP + portfolio 17** | 1.06 | 4.51 | 0.15 |
| **CRSP + portfolio 18** | 1.10 | 4.63 | 0.15 |
| **CRSP + portfolio 19** | 1.18 | 4.74 | 0.17 |
| **CRSP + portfolio 20** | 1.22 | 4.95 | 0.17 |
| **CRSP + portfolio 21** | 1.29 | 5.23 | 0.17 |
| **CRSP + portfolio 22** | 1.34 | 5.83 | 0.16 |
| **CRSP + portfolio 23** | 1.33 | 5.71 | 0.17 |
| **CRSP + portfolio 24** | 1.37 | 6.41 | 0.15 |
| **CRSP index** | 0.88 | 4.43 | 0.11 |

*Notes:* This table reports construction details for long only aggregate portfolios formed by combining the CRSP index with long only zeta risk portfolios formed on $Z^*_{i,a}$ coefficients estimated in the empirical ZCAPM. A total of 24 long zeta risk portfolios are formed. Long aggregate portfolios are created using a 50% weight for the CRSP index and 50% weight for each long zeta risk portfolio. For 648 months in the analysis period January 1965 to December 2018, we report for each long aggregate portfolio the average one-month-ahead return denoted as $\bar{R}_{CRSPt+1} + \bar{R}_{pt+1}$, time-series standard deviation of this aggregate monthly return series denoted as $\sigma_{CRSP+p,t+1}$, and the Sharpe ratio. For comparison purposes, results for the CRSP index are shown.

---

Table 9.5 gives results for the 24 long only aggregate portfolios formed by combining the proxy minimum variance portfolio $g$ with the 24 long only zeta risk portfolios. Combining $g$ with portfolios 8 to 24 yields Sharpe ratios between 0.12 and 0.20, which are higher than the CRSP index at 0.11 as well as the corresponding aggregate portfolios formed using the CRSP index in Table 9.4. Among high risk portfolios, combining $g$ with long only portfolios 22, 23, and 24 earns relatively high average returns of 1.38%, 1.37%, and 1.41%, respectively, which again exceed average returns for the CRSP index as well as corresponding aggregate portfolios containing the CRSP index. Notice that the following portfolios are better proxies for market returns than the CRSP index: portfolio $g$ plus long only portfolios 13 and 14. These two portfolios have the lowest total risk at 4.00% (compared to 4.39% in Table 9.4 using the CRSP index) but earn 0.98% and 1.02% (compared to 0.94% and 0.98% in Table 9.4) per month.

#### Table 9.5: Construction details for long only aggregate portfolios composed of the proxy minimum variance portfolio $g$ plus long only zeta risk portfolio

| Long aggregate portfolios | $\bar{R}_{gt+1} + \bar{R}_{pt+1}$ (%) | $\sigma_{g+p,t+1}$ (%) | Sharpe ratio |
| :--- | :---: | :---: | :---: |
| **Min var portfolio $g$ + portfolio 1** | 0.24 | 6.88 | −0.02 |
| **Min var portfolio $g$ + portfolio 2** | 0.29 | 6.56 | −0.02 |
| **Min var portfolio $g$ + portfolio 3** | 0.40 | 6.04 | 0.00 |
| **Min var portfolio $g$ + portfolio 4** | 0.68 | 5.24 | 0.06 |
| **Min var portfolio $g$ + portfolio 5** | 0.74 | 4.88 | 0.07 |
| **Min var portfolio $g$ + portfolio 6** | 0.84 | 4.62 | 0.10 |
| **Min var portfolio $g$ + portfolio 7** | 0.87 | 4.47 | 0.11 |
| **Min var portfolio $g$ + portfolio 8** | 0.89 | 4.33 | 0.12 |
| **Min var portfolio $g$ + portfolio 9** | 0.92 | 4.20 | 0.13 |
| **Min var portfolio $g$ + portfolio 10** | 0.96 | 4.11 | 0.14 |
| **Min var portfolio $g$ + portfolio 11** | 0.95 | 4.07 | 0.14 |
| **Min var portfolio $g$ + portfolio 12** | 0.95 | 4.05 | 0.14 |
| **Min var portfolio $g$ + portfolio 13** | 0.98 | 4.00 | 0.15 |
| **Min var portfolio $g$ + portfolio 14** | 1.02 | 4.00 | 0.16 |
| **Min var portfolio $g$ + portfolio 15** | 1.04 | 4.02 | 0.16 |
| **Min var portfolio $g$ + portfolio 16** | 1.04 | 4.07 | 0.16 |
| **Min var portfolio $g$ + portfolio 17** | 1.10 | 4.11 | 0.17 |
| **Min var portfolio $g$ + portfolio 18** | 1.13 | 4.22 | 0.18 |
| **Min var portfolio $g$ + portfolio 19** | 1.21 | 4.31 | 0.19 |
| **Min var portfolio $g$ + portfolio 20** | 1.26 | 4.51 | 0.19 |
| **Min var portfolio $g$ + portfolio 21** | 1.33 | 4.77 | 0.20 |
| **Min var portfolio $g$ + portfolio 22** | 1.38 | 5.35 | 0.19 |
| **Min var portfolio $g$ + portfolio 23** | 1.37 | 5.24 | 0.19 |
| **Min var portfolio $g$ + portfolio 24** | 1.41 | 5.94 | 0.17 |
| **Min var portfolio $g$** | 0.96 | 3.49 | 0.16 |

*Notes:* This table reports construction details for long only aggregate portfolios formed by combining the proxy minimum variance portfolio $g$ with long only zeta risk portfolios formed on $Z^*_{i,a}$ coefficients estimated in the empirical ZCAPM. Portfolio $g$ is developed from the empirical ZCAPM. A total of 24 long zeta risk portfolios are formed. Long aggregate portfolios are created using a 50% weight for portfolio $g$ and 50% weight for each long zeta risk portfolio. For 648 months in the analysis period January 1965 to December 2018, we report for each long aggregate portfolio the average one-month-ahead return denoted as $\bar{R}_{gt+1} + \bar{R}_{pt+1}$, time-series standard deviation of this aggregate monthly return series denoted as $\sigma_{g+p,t+1}$, and Sharpe ratio. For comparison purposes, results for portfolio $g$ are shown.

---

Figure 9.6 shows frontier estimates for these 24 long only aggregate portfolios created by combining proxy minimum variance portfolio $g$ with each of the 24 long only zeta risk portfolios.

![Fig. 9.6](images/fig9_6.jpg)  
*Fig. 9.6: Frontier estimates are shown based on average one-month-ahead (out-of-sample) returns and the time-series standard deviation of these returns for 24 long only aggregate portfolios. These long aggregate portfolios are formed by investing 50% of funds in the proxy minimum variance portfolio $g$ and 50% of funds in 24 long zeta risk portfolios. Visual comparisons can be made to the CRSP market index and proxy minimum variance portfolio $g$. The analysis period is January 1965 to December 2018.*

Figures 9.5 and 9.6 visually summarize our long only aggregate portfolio findings. By combining market indexes with long only zeta risk portfolios, we can create aggregate portfolios with only long positions that outperform the CRSP index. Also, these long only aggregate portfolios trace out a mean-variance parabolic shape that is similar to aggregate portfolios with long/short positions in Fig. 9.3.

Importantly, using zeta risk, we can control the relative risks of different aggregate portfolios. For example, an investor seeking higher returns can choose an aggregate portfolio combining the market index with high zeta risk portfolios (e.g., portfolios 20–24), which earns substantially higher returns than the CRSP index with modest increases in total risk. Alternatively, a conservative investor can select an aggregate portfolio combining portfolio $g$ with portfolios 13–15, which achieves lower risk than the CRSP index while earning higher average returns.

What about other asset pricing models based on popular multifactors? Can they be used to build efficient portfolios that outperform the CRSP index? To investigate this question, we repeat the above procedures by replacing zeta risk with beta risk associated with the popular Fama–French multifactors: size ($\beta_{SMB}$), value ($\beta_{HML}$), and momentum ($\beta_{MOM}$). For each multifactor, individual stocks are ranked in the one-year estimation period based on their estimated factor beta, and 12 long/short beta risk portfolios are formed. Each long/short factor portfolio is then combined with the CRSP index to form aggregate portfolios, and their out-of-sample monthly returns are tracked from 1965 to 2018.

The results are summarized in Fig. 9.7. It is obvious from this figure that there is no relationship between risk and return when aggregate portfolios are formed using beta risk associated with the popular multifactors $SMB$, $HML$, and $MOM$. For each factor, the 12 aggregate portfolios plot in flat lines well below the frontier produced by combining the CRSP index with long/short portfolios based on zeta risk.

![Fig. 9.7](images/fig9_7.jpg)  
*Fig. 9.7: The graph compares average one-month-ahead (out-of-sample) returns and the time-series standard deviation of these returns for: (1) aggregate portfolios comprised of the CRSP market index (denoted a) plus 12 long/short zeta risk portfolios, and (2) aggregate portfolios comprised of the CRSP market index (denoted a) plus 12 long/short beta risk portfolios based on sensitivity to the popular multifactors size ($SMB$), value ($HML$), and momentum ($MOM$). The analysis period is January 1965 to December 2018.*

The flat lines in Fig. 9.7 demonstrate that multifactor betas do not generate compensation for bearing systematic risk in out-of-sample tests. In contrast to our long/short zeta risk portfolios, which generate an upward sloping frontier where higher risk corresponds to higher return, aggregate portfolios based on multifactor betas fail to increase returns as risk increases. These results indicate that factor premiums associated with size, value, and momentum reflect static characteristics or data-mining artifacts rather than priced systematic risk. Long/short portfolios based on multifactor betas cannot be used to financially engineer efficient investment portfolios.

---

## 9.5 Summary

This chapter applied the ZCAPM asset pricing model to the problem of constructing superior performing stock portfolios. According to the ZCAPM, expected asset returns are a function of beta risk related to average market returns and zeta risk associated with cross-sectional return dispersion (RD). Given beta-adjusted market returns, as RD increases, assets with positive (negative) sensitivity to RD will tend to have increasing (decreasing) returns, and vice versa as RD decreases. In this regard, as previously proven in Chapters 3 and 4 but previously unknown, the mean-variance investment parabola of Markowitz (1959) is defined by the average market return (e.g., CRSP index return) on the axis of symmetry and RD related to its width. In view of these new insights about the investment parabola, to earn stock portfolio returns greater than a general market index return, we added portfolios with different levels of sensitivity to RD to the CRSP market index. No precedent exists in the literature for this investment portfolio strategy, which is motivated by our previously unknown findings about the parabola and related ZCAPM asset pricing model.

Applying the expectation–maximization (EM) algorithm to estimate the empirical ZCAPM for U.S. stocks, zeta risk coefficients (i.e., sensitivity to return dispersion) were estimated for all stocks in a one year period with daily returns. Stocks were ranked on their zeta risk estimates and formed into 24 portfolios. These portfolios were used to construct 12 long/short portfolios that stratify zeta risk into slices ranging from high to low. One-month-ahead (out-of-sample) returns for the portfolios were computed. This process was repeated over time to generate a monthly series of returns for all portfolios from January 1965 to December 2018. Strikingly, for stocks in the top $+1\%/\text{bottom } -1\%$, top $+2\%/\text{bottom } -2\%$, and top $+5\%/\text{bottom } -5\%$ of estimated zeta risk coefficients, average returns in the post-formation month equaled 2.34%, 2.16%, and 1.96%, respectively, which are exceptional for long/short portfolios. More generally, supporting the ZCAPM’s ability to capture market risk, a strong positive and linear relation between one-month-ahead returns and zeta risk was documented.

Next, we combined the CRSP value-weighted index with our 12 zero-investment RD portfolios to form 12 aggregate zeta risk portfolios. The latter aggregate portfolios’ post-formation, one-month-ahead returns traced out an upward sloping frontier earning one-month-ahead returns in the range of 0.95% to 3.22% per month as zeta risk increases. Additionally, we constructed long only aggregate portfolios by combining the CRSP index with portfolios containing different levels of zeta risk. These aggregate portfolios earned average returns in the analysis period from 0.20% to 1.37% per month depending on different levels of zeta risk.

We conjectured that more efficient aggregate portfolios could be created by combining minimum variance portfolio $G$ with zeta risk portfolios. For this purpose, we used the empirical ZCAPM to estimate a proxy for the theoretical $G$ denoted $g$ that contains most stocks in the U.S. stock market. Portfolio $g$ was constructed to have both low zeta risk and low idiosyncratic risk. Out-of-sample returns for portfolio $g$ were computed from January 1965 to December 2018. Substituting our $g$ portfolio for the CRSP index, another set of aggregate portfolios was formed by adding the 12 long/short zeta risk portfolios. As anticipated, these aggregate portfolios were more efficient than those based on the CRSP index. For example, holding total risk similar to the CRSP index, an average monthly return of 1.75% was earned. This exceptional return performance is approximately 100% higher than the CRSP index at 0.88%. The highest earning aggregate portfolio achieved an average monthly return of 3.30% but at the cost of higher total risk.

Related to these tests, average Sharpe ratios ranged from 0.13 to 0.33 across our 12 aggregate portfolios based on the CRSP index and 0.18 to 0.36 across 12 aggregate portfolio with the $g$ portfolio. These average Sharpe ratios clearly dominated the CRSP index at 0.11 in our analysis period. Gibbons et al. (1989) test statistics based on Sharpe ratios indicated that both of our aggregate zeta risk portfolios—namely, those based on the CRSP index plus 12 long/short zeta portfolios as well as proxy portfolio $g$ plus the 12 long/short zeta risk portfolios—are highly significant. By inference, the CRSP index is relatively inefficient compared to our aggregate portfolios. Also, GRS tests showed that our aggregate portfolios could not be explained by the Fama and French six-factor model.

Further robustness tests found that different levels of beta risk associated with popular size, value, and momentum factors were not useful in creating aggregate portfolios that outperform the CRSP index.

We conclude that the sensitivity of stock returns to cross-sectional return dispersion in the stock market enables the creation of superior performing diversified portfolios. Further research is recommended on international stocks as well as other asset classes, including bonds, commodities, real estate, etc., to replicate our findings in other samples.

An important implication of our findings is that practitioners can use our methods to develop zeta risk portfolios and aggregate portfolios. Prudence would advise paper trading tests incorporating trading costs of rebalancing portfolios from month to month. Also, experiments with long only and long/short portfolios should be conducted. Assuming these tests were successful, new investment products could be created for customers. Products that span a wide array of total risk levels would enable customers to choose products that best fit their risk preferences. As shown by our results, lower (higher) risk portfolios earn lower (higher) returns on average over time, thus enabling managers to control relative risk and return outcomes available to customers. A caveat here is that our portfolio methods require investment horizons of at least three-to-five years. In earlier paper trading tests performed by the authors in cooperation with the Teachers Retirement System of Texas, based on backtesting over about 20 years, we found that aggregate long only portfolios using the same stocks as in the S&P 500 index outperformed this index in almost all three-year periods of time. Hence, our ZCAPM approach to building stock portfolios is a long-run investment strategy.

Lastly, we would like to emphasize that the investment technology presented in this chapter is more practitioner than academic oriented. Much academic research is devoted to various anomalous portfolio returns not explained by asset pricing models. For example, as discussed in the previous Chapter 8, many studies have documented anomalous returns associated with momentum. Little or no theory helps to explain abnormally high momentum returns. Most momentum studies form long/short portfolios using the top/bottom deciles of stocks in terms of average return performance over the past year. More consistent with prudential investment practices, we form a wide variety of long/short portfolios that span different risk levels (rather than choosing portfolios based solely on returns with little or no consideration of risk). We subsequently add our long/short zeta risk portfolios to an aggregate index (such as the CRSP index or minimum variance $g$ portfolio) to form new aggregate portfolios with different risk levels. In both long/short zeta risk portfolios and aggregate portfolios incorporating these zero-investment portfolios, our methods are more consistent with the practice of prudent risk management in professional investment services than the search for anomalous returns in academic literature.

---

## Footnotes

[^1]: See also Liu et al. (2012) and Liu (2013).
[^2]: See also Liu et al. (2020).
[^3]: As discussed in Chapter 4, we set the intercept parameter $\alpha_i$ to zero for several reasons. In the present case, our interest is in out-of-sample returns of zero-investment and aggregate portfolios based on zeta risk, rather than their in-sample returns in Eq. (9.2).
[^4]: See Chapter 4 for detailed instructions on how to estimate the empirical ZCAPM using the EM algorithm. Further citations to related finance and statistics literature are provided there also.
[^5]: Related work by Ang et al. (2006) constructed a volatility mimicking factor based on innovations in the VIX (i.e., the Chicago Board Options Exchange’s CBOE Volatility Index). The VIX attempts to measure the market’s expectation of 30-day volatility, which is a time-series market volatility measure rather than cross-sectional return dispersion measure.
[^6]: These returns should be primarily attributable to zeta risk, as the betas of diversified long and short portfolios will be near one and cancel out for the most part.
[^7]: Alternatively, what if the brokerage does not allow you to form the zero-investment, long/short portfolio without cash collateral? Now you can only buy $\\$50$ of the CRSP index and another $\\$50$ long/short, such that your monthly return is $(\\$1 + \\$1.5)/\\$100 = 2.5\%$. This portfolio is not leveraged. In forthcoming analyses we allow leveraged positions.
[^8]: Numerous studies have documented that efficient portfolios as proposed by Markowitz (1959) contain short positions (e.g., Pulley 1981; Levy 1983; Kallberg and Ziemba 1983; Kroll et al. 1984; Green and Hollifield 1992; Jagannathan and Ma 2003; Brennan and Lo 2010; Levy and Ritov 2010). Strong theoretical support for short positions in efficient portfolios is provided by Brennan and Lo (2010), who proved that mean-variance efficient frontiers with long only portfolios are virtually impossible. More generally, Kothari (1995) have argued that the equity portfolio most highly correlated with the market portfolio is efficient.
[^9]: As mentioned above, we drop low volatility stocks with less than 20% of the CRSP index in the one year estimation period. This filter eliminates stocks that would receive relatively large weights and bias our construction of proxy portfolio $g$.
[^10]: For example, upon experimenting with different undiversified momentum strategies, Jegadeesh and Titman (1993, p. 70) obtained an abnormally high average return of 1.49% per month for a momentum portfolio based on top/bottom 5% deciles of winner and loser stocks and 6-month formation and 6-month holding periods. Other researchers have documented that these abnormally high momentum returns are subject to momentum crashes with large losses (e.g., see Barroso and Santa-Clara 2015; Daniel and Moskowitz 2016). Barroso and Santa-Clara (2015) and Daniel and Moskowitz (2016) have shown that risk management strategies can mitigate momentum crashes to some extent.
[^11]: Polson and Tew (2000) used a Bayesian approach in combination with hierarchical models to estimate predicted expected returns and variance-covariance matrices for stocks. These estimates were used to optimize portfolio weights in the S&P 500 index from January 1970 to December 1996. In their study, the value-weighted S&P 500 index earned on average 1.02% per month compared to 1.17% for their optimized portfolio containing S&P 500 index stocks. They did not provide information on the return volatility or Sharpe ratios of different aggregate portfolios. See also related work on estimation risk and portfolio selection by Klein and Bawa (1976) and Jorion (1986). Moreover, Levy and Roll (2010) have shown that small variations in the mean-variance parameters of assets within a typical market proxy portfolio can yield more efficient market indexes.

---

## Appendix: Bibliography (Book pp. 256–258)

- Ang, A., Hodrick, R. J., Xing, Y., & Zhang, X. (2006). The cross-section of volatility and expected returns. *Journal of Finance*, 61, 259–299.
- Barras, L., Scaillet, O., & Wermers, R. (2010). False discoveries in mutual fund performance: Measuring luck in estimated alphas. *Journal of Finance*, 65, 179–216.
- Barroso, P., & Santa-Clara, P. (2015). Momentum has its moments. *Journal of Financial Economics*, 116, 111–120.
- Black, F. (1972). Capital market equilibrium with restricted borrowing. *Journal of Business*, 45, 444–454.
- Bollen, N., & Busse, J. (2004). Short-term persistence in mutual fund performance. *Review of Financial Studies*, 18, 569–597.
- Brennan, T. J., & Lo, W. W. (2010). Impossible frontiers. *Management Science*, 56, 905–923.
- Carhart, M. M. (1997). On persistence in mutual fund performance. *Journal of Finance*, 52, 57–82.
- Daniel, K. (2011). Momentum crashes (Working Paper). Columbia University.
- Daniel, K., & Moskowitz, T. (2016). Momentum crashes. *Journal of Financial Economics*, 122, 221–247.
- Dempster, A. P., Laird, N. M., & Rubin, D. B. (1977). Maximum likelihood from incomplete data via the EM algorithm. *Journal of the Royal Statistical Society*, 39, 1–38.
- Fama, E. F. (1970). Efficient capital markets: A review of theory and empirical work. *Journal of Finance*, 25(2), 383–417.
- Fama, E. F., & French, K. R. (1992). The cross-section of expected stock returns. *Journal of Finance*, 47, 427–465.
- Fama, E. F., & French, K. R. (1993). The cross-section of expected returns. *Journal of Financial Economics*, 33, 3–56.
- Fama, E. F., & French, K. R. (1995). Size and book-to-market factors in earnings and returns. *Journal of Finance*, 50, 131–156.
- Fama, E. F., & French, K. R. (2004). The capital asset pricing model: Theory and evidence. *Journal of Economic Perspectives*, 18(3), 25–46.
- Fama, E. F., & French, K. R. (2010). Luck versus skill in the cross-section of mutual fund returns. *Journal of Finance*, 65, 131–156.
- Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*, 116, 1–22.
- Fama, E. F., & French, K. R. (2018). Choosing factors. *Journal of Financial Economics*, 128, 234–252.
- Fama, E. F., & MacBeth, J. D. (1973). Risk, return, and equilibrium: Empirical tests. *Journal of Political Economy*, 81, 607–636.
- Gibbons, M. R., Ross, S. A., & Shanken, J. (1989). A test of the efficiency of a given portfolio. *Econometrica*, 57, 1121–1152.
- Green, R. C., & Hollifield, B. (1992). When will mean-variance efficient portfolios be well diversified? *Journal of Finance*, 47, 1785–1809.
- Jagannathan, R., & Ma, T. (2003). Risk reduction in large portfolios: A role for portfolio weight constraints. *Journal of Finance*, 58, 1651–1684.
- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. *Journal of Finance*, 48, 65–91.
- Jegadeesh, N., & Titman, S. (2001). Profitability of momentum strategies: An evaluation of alternative explanations. *Journal of Finance*, 56, 699–720.
- Jensen, M. C. (1968). The performance of mutual funds in the period 1945–1964. *Journal of Finance*, 23, 389–416.
- Jorion, P. (1986). Bayes-Stein estimation for portfolio analysis. *Journal of Financial and Quantitative Analysis*, 21, 279–292.
- Kallberg, J. G., & Ziemba, W. T. (1983). Comparison of alternative utility functions in portfolio selection problems. *Management Science*, 29, 1257–1276.
- Klein, R. W., & Bawa, B. S. (1976). The effect of estimation risk on optimal portfolio choice. *Journal of Financial Economics*, 3, 215–231.
- Kothari, S. P., Shanken, J., & Sloan, R. G. (1995). Another look at the cross-section of expected stock returns. *Journal of Finance*, 50, 185–224.
- Kroll, Y., Levy, H., & Markowitz, H. (1984). Mean-variance versus direct utility maximization. *Journal of Finance*, 39, 47–61.
- Levy, H. (1983). The capital asset pricing model: Theory and empiricism. *Economic Journal*, 93, 145–165.
- Levy, M., & Ritov, Y. (2010). Mean-variance efficient portfolios with many assets: 50% short. *Quantitative Finance*, 11, 1461–1471.
- Levy, M., & Roll, R. (2010). The market portfolio may be mean/variance efficient after all. *Review of Financial Studies*, 23, 2464–2491.
- Liu, W. (2013). A new asset pricing model based on the zero-beta CAPM: Theory and evidence. Doctoral dissertation, Texas A&M University.
- Liu, W., Kolari, J. W., & Huang, J. Z. (2012, October). A new asset pricing model based on the zero-beta CAPM. Presentation at the annual meetings of the Financial Management Association, Atlanta, GA.
- Liu, W., Kolari, J. W., & Huang, J. Z. (2020, October). Return dispersion and the cross-section of stock returns. Presentation at the annual meetings of the Southern Finance Association, Palm Springs, CA.
- Malkiel, B. G. (1995). Returns from investing in equity mutual funds 1971 to 1991. *Journal of Finance*, 50, 549–572.
- Malkiel, B. G. (2005). Reflections on the efficient market hypotheses: 30 years later. *The Financial Review*, 40, 1–9.
- Markowitz, H. M. (1959). *Portfolio selection: Efficient diversification of investments*. New York, NY: Wiley.
- Polson, N. G., & Tew, B. V. (2000). Bayesian portfolio selection: An empirical analysis of the S&P 500 index 1970–1996. *Journal of Business and Economic Statistics*, 18, 164–173.
- Pulley, L. B. (1981). General mean-variance approximation to expected utility for short holding periods. *Journal of Financial and Quantitative Analysis*, 16, 361–373.
- Sharpe, W. F. (1964). Capital asset prices: A theory of market equilibrium under conditions of risk. *Journal of Finance*, 19, 425–442.
