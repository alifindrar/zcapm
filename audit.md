# Building Portfolios Based on Zeta Risk

We use all U.S. stocks in the intersection of the NYSE, AMEX, and NASDAQ return files from the Center for Research in Security Prices (CRSP) in the period January 1964 to December 2018. Relatively small firms with market capitalization in the bottom 10% at year-end are dropped in the next year. Daily CRSP value-weighted returns and Treasury bill rates are used to proxy mean market returns ($R_{at}$) and riskless returns ($R_{ft}$), respectively. To proxy the cross-sectional standard deviation of assets' returns (i.e., RD), value-weighted returns for $i = 1, \ldots, n$ assets on day $t$ ($R_{it}$) are used to compute

$$
\tilde{\sigma}_{at} = \sqrt{\frac{n}{n-1}\sum_{i=1}^{n} w_{it-1}\left(\tilde{R}_{it}-\tilde{R}_{at}\right)^{2}}, \tag{9.5}
$$

where $w_{it}$ = the market value weight for asset $i$. Within our analysis period January 1965 to December 2018, the mean daily RD of stocks in the CRSP index equals 1.81%, and the mean daily CRSP return of 0.04%. Hence, cross-sectional market RD is large in magnitude relative to mean market returns on any given day $t$. Relevant to later evaluating the performance of aggregate portfolios constructed using the empirical ZCAPM, the mean monthly CRSP return and standard deviation of CRSP monthly returns throughout our analysis period equal 0.88% and 4.44%, respectively (see Table 5.1 in Chapter 5).

We begin by utilizing the sensitivity of stocks to RD movements (i.e., zeta risk) to construct zero-investment portfolios.<sup>5</sup> The following steps are used to build a variety of zero-investment (long/short) stock portfolios with different zeta risk levels.

1. Times-series regressions are used to estimate empirical ZCAPM Eq. (9.4) via the expectation–maximization (EM) algorithm for all individual stocks with daily returns for the initial 12-month estimation period January to December 1964.
2. All stocks are ranked in terms of their estimated zeta coefficient $\hat{Z}^*_{i,a}$.
3. A total of 24 portfolios are formed from positive to negative zeta risk. Equal-weighted returns are computed for each portfolio in the next month January 1965 (i.e., out-of-sample returns).
4. Using these portfolios, 12 zero-investment portfolios are formed with one long and one short portfolio.
   - (a) Portfolios 1 and 2 are zero-investment portfolios that are long/short in stocks with high zeta market risk $\hat{Z}^*_{i,a}$, in the top +1%/bottom −1% and top +2%/bottom −2% of all sample stocks, respectively. We form these tail portfolios to better understand extreme risk/return profiles associated with RD.
   - (b) Portfolios 3 to 12 are comprised of long/short stocks in incremental +5/−5% portfolios with respect to zeta risk $\hat{Z}^*_{i,a}$. More specifically, portfolio 3 contains the top +5/−5% stocks with relatively high zeta risk coefficients, portfolio 4 contains the next +5/−5% of stocks per their zeta risk coefficients, ..., portfolio 12 contains the bottom +5/−5% stocks with zeta risk coefficients near zero.
5. For all stocks in each long/short zeta risk portfolio, we compute the one-month-ahead (out-of-sample), equal-weighted portfolio holding period return $R_{pt+1}$ in January 1965.<sup>6</sup> This out-of-sample approach mimics actual investor behavior in terms of forming portfolios at time $t = T$ and then observing their performance in the next month $T + 1$.
6. The above process is repeated by rolling the estimation period in step (1) forward one month at a time to rebalance the zero-investment, return dispersion portfolios until their last one-month-ahead holding period returns are computed in December 2018. The time-series standard deviation of these 648 out-of-sample portfolio returns in the analysis period January 1965 to December 2018 is computed also.

Our 12 zero-investment portfolios based on zeta risk span a wide range of market risk associated with cross-sectional RD. If there is a relation between one-month-ahead returns and zeta risk loadings, average returns should increase from low for portfolio 12 to high for portfolio 1.

We build aggregate zeta risk portfolios by combining the value-weighted CRSP index with each of the 12 zero-investment, zeta risk portfolios. Aggregate portfolios have weights for all CRSP stocks that add to one plus a positive weight for the long/short zeta risk portfolios. Post-formation, one-month-ahead returns are computed for these aggregate zeta risk portfolios from January 1965 to December 2018. As an example to clarify our assumptions, suppose that you have $100 dollars and buy the CRSP index that earns the average market return. At the same time, your brokerage firm allows you to buy $100 stocks (long) and sell $100 stocks (short) in a long/short portfolio (i.e., a positive constant 1 is assigned as the weight for the long/short zeta risk portfolio). After one month, the CRSP index generates $2 and the long/short portfolio earns $3, such that your total return is ($2 + $3)/$100 = 5%. This aggregate portfolio is leveraged.<sup>7</sup>

Previous studies have shown that short positions are needed to create more efficient portfolios.<sup>8</sup> However, a criticism of this approach is that many investors only hold long portfolios (e.g., pension funds, mutual funds, etc.). Accordingly, we also examine the average performance of the 24 zeta risk portfolios with long only positions. Moreover, we build 24 long only aggregate portfolios by investing 50% of funds in the CRSP index and 50% in each long zeta risk portfolio, which enables insights into the effects of restricting aggregate portfolios to long only positions compared to allowing short positions.

Lastly, we build another set of aggregate portfolios based on a proxy for the theoretical minimum variance portfolio $G$ denoted $g$. As discussed in Chapter 3, the CRSP index lies on the axis of symmety of the mean-variance parabola and therefore is not an efficient portfolio. A more efficient general market index is the portfolio $G$ located at the vertex of the parabola. To develop a proxy $g$ portfolio from the empirical ZCAPM, we reduce both idiosyncratic and zeta risks (i.e., $g$ has little or no zeta risk as it is unaffected by return dispersion that defines the width of the investment parabola per our findings in Chapters 3 and 4). As in the case of the zeta risk portfolios, we drop the lowest 10% of stocks by market capitalization at year-end in the subsequent year. Also, we drop stocks with standard deviations of monthly returns in each one-year estimation period less than 20% of the CRSP index. This volatility filter eliminates stocks in each estimation window with volatility less than a highly diversified market index. These stocks are likely very illiquid or have other issues that are idiosyncratic (i.e., firm specific) in nature. To build portfolio $g$, we follow steps similar to the construction of the 24 zeta risk portfolios.

1. Times-series regressions are used to estimate the empirical ZCAPM Eq. (9.4) via the expectation–maximization (EM) algorithm for all individual stocks with daily returns for the initial 12-month estimation period January to December 1964.
2. To reduce idiosyncratic and zeta risks, all stocks are weighted as $w_i = \dfrac{1}{0.01 + |\hat{Z}^*_{i,a}|} \times \dfrac{1}{\operatorname{var}(u_{it})}$, where idiosyncratic risk is measured by the variance of the residual error terms denoted $\operatorname{var}(u_{it})$, and 0.01 is added to the absolute value of the estimated zeta risk coefficient $\hat{Z}^*_{i,a}$ to avoid the case of singularity when $\hat{Z}^*_{i,a} = 0$.<sup>9</sup>
3. For all stocks, we compute the one-month-ahead, weighted portfolio holding period return $R_{gT+1}$ in January 1965.
4. The above process is repeated by rolling the estimation period in step (1) forward one month at a time to rebalance portfolio $g$ until the last one-month-ahead holding period return is computed in December 2018.

As in the case of the CRSP index, aggregate portfolios are formed by combining proxy minimum variance portfolio $g$ with the 12 long/short zeta risk portfolios.

# MATLAB Programs

This compendium provides Matlab programs for analyses in this book. The programs are used to: (1) estimate the empirical ZCAPM, and (2) conduct cross-sectional regression tests of the empirical ZCAPM. The expectation-maximization (EM) algorithm is employed to estimate ZCAPM regression model parameters.

If the cross-sectional tests are not needed, you can output the empirical ZCAPM regression results. To do this, uncomment code in the `main.m` file by removing the percentage symbol: `%xlswrite('ts_coeff',ts_coeff)`. The results will be stored in an excel file called `ts_coeff`. In this file, the first column is beta ($\beta$), second column is zeta ($Z$), and third column is the probability ($p$) that $Z$ is positive in sign. To get $Z^*$, simply calculate $Z(2p-1)$. The scale of $Z^*$ is for daily returns. To convert to a monthly return scale, simply multiply $Z^*$ by 21 as used in our codes (see Eq. (5.5) in Chapter 5).

## main.m

- The main function of the program, which assigns the start date and prediction window, calculates cross-sectional regression estimates for $\lambda_a$ and $\lambda_{RD}$ and their t-statistics in the second step of the Fama and MacBeth procedure, and outputs results (i.e., the filename is named `results`). Run this file to start all codes.
- Called by: n/a
- Calls: `ana.m`, `get_rsq.m`
- The `%` symbol comments out code or wording from being run in the Matlab program. Code can be uncommented by removing this symbol.

```matlab
function main()
date_start=196501;
%date_start=199001; %%%% second half for split data results
holding_unit=[1,3,6,9,12,24]; %%%% number of months rolled forward each time
num_roll_window=[6,12]; %%%% number of months used to estimate beta and zeta
for ii=2:2
    roll_window_mon=num_roll_window(ii);
    for j=1:1
        holding_mon=holding_unit(j);
        [ts_coeff, ts_coeff1,cs_coeff,ret_mon,factors_a]...
            =ana(date_start,roll_window_mon,holding_mon);
        %%%%% rolling month approach
        dim=size(cs_coeff);
        [rsq,beta,t_stat,t1]=get_rsq(ts_coeff1,ret_mon,factors_a); %%%% single regression to get R2
        %%%% The following codes calculate the average estimates of λa and λRD, their t-statistics, and other outputs that appear in the results file %%%%
        num_para=(dim(2)-1)/2;
        results=NaN(2*num_para+1,2+1);
        for i=1:num_para
            results(i,1)=mean(cs_coeff(:,2*i-1));
            results(i,2)=results(i,1)/std(cs_coeff(:,2*i-1))*sqrt(dim(1)-1);
        end
        %output shanken test
        results(5,3)=t1(1);
        results(6,3)=t1(2);
        results(7,3)=t1(3);
        results(num_para+1,1)=rsq;
        results(num_para+2,1:2)=[beta(1),t_stat(1)];
        results(num_para+3,1:2)=[beta(2),t_stat(2)];
        results(num_para+4,1:2)=[beta(3),t_stat(3)];
        xlswrite('results',results);
        %xlswrite('ts_coeff',ts_coeff); %%% output time-series regression results for empirical ZCAPM
        %xlswrite('cs_coeff',cs_coeff);
        %xlswrite('ret_mon',ret_mon)
    end
end
```

## ana.m

- The workhorse of the program, this subroutine generates coefficients which are then used in both `main.m` and `get_rsq.m` to output the final beta, zeta, and t-statistic outputs.
- Called by: `main.m`
- Calls: `read_etf_data.m`, `read_factors.m`, `scan_data_struct.m`, `solve_hidden_variable_v2.m`, `cross_section_reg.m`, and `gen_cul_ret.m`

```matlab
function [ts_coeff, ts_coeff1,cs_coeff,ret_mon,factors_a]...
    =ana(date_start,roll_window,holding_mon)
[ff25,ind47,own25,bm100,bmop25,bminv25,opinv25]=read_etf_data;
%%%% Read Excel data files containing daily returns of test asset portfolios %%%%
%%%% Choose different test assets, change as your data structure changes %%%%
%%%% Only one stock_ret= should be uncommented at a time %%%%
stock_ret=ff25;
%stock_ret=ind47;
%stock_ret=own25;
%stock_ret=[ff25,ind47(:,2:48)];
%stock_ret=[ff25,ind47(:,2:48),own25(:,2:26)];
%stock_ret=bm100;
%stock_ret=bm100(:,1:21); %%%% bottom 20
%stock_ret=[bm100(:,1),bm100(:,22:end)]; %%%%% top 80
%stock_ret=bm100(:,1:51); %%%% bottom 50
%stock_ret=[bm100(:,1),bm100(:,52:end)]; %%%% bottom 50
%stock_ret=bmop25;
%stock_ret=bminv25;
%stock_ret=opinv25;
%%%% Split data in half (as robustness check using subperiods) %%%%
%stock_ret=ff25(1:6538,:);
%stock_ret=ff25(6287:end,:);
%stock_ret=ind47(1:6538,:);
%stock_ret=ind47(6287:end,:);
%stock_ret=own25(1:6538,:);
%stock_ret=own25(6287:end,:);
%stock_ret=[ff25(1:6538,:),ind47(1:6538,2:48)];
%stock_ret=[ff25(6287:end,:),ind47(6287:end,2:48)];
%stock_ret=[ff25(1:6538,:),ind47(1:6538,2:48),own25(1:6538,2:26)];
%stock_ret=[ff25(6287:end,:),ind47(6287:end,2:48),own25(6287:end,2:26)]; %%%% using the above codes, choose different test assets or their combinations %%%%
dim_ret=size(stock_ret);
factors=read_factors;
%%%% read factors from data file
%%%% Factors for split data (optional) %%%%
%factors=factors(1:6538,:); %%%% first half
%factors=factors(6287:end,:);
%%%% second half
%%%% Get row numbers in daily data for each calendar month %%%%
[data_nm,data_str]=scan_data_struct(int32(factors(:,1)/100));
dim=size(data_nm);
for i=1:dim(1)
    if (date_start==data_nm(i,1))
        pos_i=i;
        break;
    end
end
%%%% All factors used for Shanken t-statistic if needed %%%%
factors_a=factors(data_str(pos_i-roll_window,1):data_str(dim(1)-1,2),2:4);
cs_coeff=[]; %%%% empty dataset to store results later
ts_coeff=[];
ret_mon=[];
ts_coeff1=[];
for itr_pd=pos_i:holding_mon:dim(1)
    factors_pr=factors(data_str(itr_pd-roll_window,1):data_str(itr_pd-1,2),2:4); % factors for time series regression
    regress_ret=stock_ret(data_str(itr_pd-roll_window,1):data_str(itr_pd-1,2),2:dim_ret(2));
    % return for time series regression
    out_sampl_ret_pr=stock_ret(data_str(itr_pd,1):data_str(itr_pd+holding_mon-1,2),2:dim_ret(2))...
        -factors(data_str(itr_pd,1):data_str(itr_pd+holding_mon-1,2),4)...
        *ones(1,dim_ret(2)-1); %%% return for out-of-sample month in cross-sectional regression
    coeff=solve_hidden_variable_v2(regress_ret,factors_pr);%%% time-series ZCAPM regression
    coeff_pr=[coeff(:,1),coeff(:,2).*(2*coeff(:,3)-1)*21]; %%%% 21 trading days per month
    ts_coeff_i=[ts_coeff;coeff_pr];
    %%%% output results for time-series regression only
    ts_coeff=ts_coeff_i;
    ts_coeff1_i=[ts_coeff1;coeff_pr]; %%%% time-series results used later in cross-sectional test
    ts_coeff1=ts_coeff1_i;
    out_sample_ret=gen_cul_ret(out_sampl_ret_pr);
    out_sample_mon=out_sample_ret(end,:)/holding_mon;
    %out_sample_mon=((1+out_sample_ret(end,:)/100).^(1/holding_mon)-1)*100;
    cs_coeff_pr=cross_section_reg(out_sample_mon,coeff_pr);%%%% cross-sectional regression
    ret_mon_i=[ret_mon;out_sample_mon(end,:)];
    ret_mon=ret_mon_i;
    cs_coeff_i=[cs_coeff;cs_coeff_pr];
    cs_coeff=cs_coeff_i;
end
```

## get_rsq.m

The rolling cross-sectional regression approach does not generate an R² value. In this program, time-series for $\lambda_a$ and $\lambda_{RD}$ coefficients and out-of-sample monthly returns are averaged for each stock. One cross-sectional regression is estimated to generate an R² value. Coefficients for beta and alpha are stored and output in the `main.m` file also. To adjust for the cross-correlation problem, `ols_estimator_cs_cor` is used, in which the Shanken t-statistic is computed to adjust estimation errors in betas.

- Calculates the R² value, a goodness-of-fit measure of the cross-sectional regression model.
- Called by: `main.m`
- Calls: `ols_estimator_cs_corr.m`

```matlab
function [rsq,beta_hat,t_stat,t1]=get_rsq(coeff,ret_mon,factors_a)
mean_ret=mean(ret_mon);
dim=size(ret_mon);
dim_cff=size(coeff);
mean_cff=zeros(dim(2),dim_cff(2));
for j=1:dim_cff(2)
    for i=1:dim(1)
        mean_cff(:,j)=mean_cff(:,j)+coeff((i-1)*dim(2)+1:i*dim(2),j);
    end
end
mean_cff=mean_cff/dim(1);
X=[ones(dim(2),1),mean_cff];
Y=mean_ret';
factors=factors_a(:,1:2); %%%% for Shanken t-statistic
[beta_hat,rs,t_stat,t1,u_hat]=ols_estimator_cs_corr(X,Y,ret_mon,coeff,factors);
rsq=rs;
```

## ols_estimator_cs_corr.m

- This function takes the data and calculates estimates of `beta_hat`, `rsqr`, `t_stat`, `t1`, and `u_hat` after adjusting for cross-correlation in the single regression approach. Note that `t1` computes the Shanken t-statistics to adjust errors in beta estimations.
- Called by: `get_rsq.m`
- Calls: n/a

```matlab
function [beta_hat,rsqr,t_stat,t1,u_hat]=ols_estimator_cs_corr(X,Y,ret,coeff,factors)
%%%% OLS estimation %%%%
dim_r=size(ret);
dim=size(Y);
beta_hat = inv(X'*X)*X'*Y; %%%% OLS estimation of beta
u_hat = Y - X*beta_hat; %%%% estimated residual
s = (u_hat'*u_hat)/(dim(1)-1)*inv(X'*X); %%%% estimated covariance matrix
se = sqrt(diag(s));
%%%% define variables needed for Shanken test
beta_no_cons=beta_hat(2:end,:);
sig_f=cov(factors)*21;
c=beta_no_cons'*inv(sig_f)*beta_no_cons;
dim_s=size(sig_f);
sig_f_hat=zeros(dim_s(1)+1,dim_s(2)+1);
sig_f_hat(2:end,2:end)=sig_f;
%%%% variance matrix %%%%
ss=inv(X'*X)*X'*(cov(ret)/dim_r(1))*X*inv(X'*X); %%%% adjust for correlation
ss=inv(X'*X)*X'*(cov(ret)/dim_r(1))*X*inv(X'*X)*(1+c)+sig_f_hat/dim_f(1); %%%% for Shanken t-statistic
sse= sqrt(diag(ss));
%%%% standard errors of beta_hat
sse1= sqrt(diag(ss1));
%%%% Shanken standard errors of beta_hat
t_stat = beta_hat./sse;
%%%% t-statistic for beta_hat
t1=beta_hat./sse1;
%%%% Shanken t-statistic for beta_hat
%p = 2*(1-tcdf(abs(t),dim(1)-1)); %%%% p-value for the t-statistic
y_av=0;
for i=1:dim(1)
    y_av=y_av+Y(i);
end
y_av=y_av/dim(1);
err_y=0;
for i=1:dim(1)
    err_y=err_y+(Y(i)-y_av)^2;
end
rsqr=1.0-(dim(1)-1)/(dim(1)-dim(2))*(u_hat'*u_hat)/err_y;
```

## ols_estimator.m

- This function takes the data and calculates estimates of `beta_hat`, `rsqr`, `t_stat`, and `u_hat` (simple OLS regression).
- Called by: `cross_section_reg.m`, `solve_hidden_variable_v2.m`
- Calls: n/a

```matlab
%%%% OLS estimation %%%%
dim=size(Y);
beta_hat = inv(X'*X)*X'*Y; %%%% OLS estimation of beta
u_hat = Y - X*beta_hat; %%%% estimated residual
s = (u_hat'*u_hat)/(dim(1)-1)*inv(X'*X); %%%% estimated covariance matrix
se = sqrt(diag(s)); %%%% standard errors of beta_hat
t_stat = beta_hat./se; %%%% t-statistic for beta_hat
%p = 2*(1-tcdf(abs(t),dim(1)-1)); %%%% p-value for the t-statistic
y_av=0;
for i=1:dim(1)
    y_av=y_av+Y(i);
end
y_av=y_av/dim(1);
err_y=0;
for i=1:dim(1)
    err_y=err_y+(Y(i)-y_av)^2;
end
rsqr=1.0-(dim(1)-1)/(dim(1)-dim(2))*(u_hat'*u_hat)/err_y;
```

## cross_section_reg.m

- This function manipulates two data sets within `ana.m` to create a row of data with 7 values, consisting of `beta_hat`, `t_stat`, and `rs` values. It estimates the cross-sectional OLS regression in the second step of the Fama and MacBeth procedure after reading parameters from the time-series empirical ZCAPM regression.
- Called by: `ana.m`
- Calls: `ols_estimator.m`

```matlab
function coeff=cross_section_reg(assets,factors_pr)
dim=size(assets);
dim_f=size(factors_pr);
%%%% Cross-sectional regression %%%%
coeff=zeros(1,2*dim_f(2)+3);
X=[ones(dim(2),1),factors_pr];
Y=assets';
[beta_hat,rs,t_stat,u_hat]=ols_estimator(X,Y);
for i=1:dim_f(2)+1
    coeff(1,2*i-1)=beta_hat(i);
    coeff(1,2*i)=t_stat(i);
end
coeff(1,2*dim_f(2)+3)=rs;
```

## solve_hidden_variable_v2.m

- This function is called in `ana.m` within a for loop. The function selects a slice of data to be processed through this function. Once this data is processed, output is continually stacked in a column in `ana.m` for final data matrix output to go to `main.m`. The output is a 3 element row of data, where the first two elements are the `beta_hat` values, and the third element is a probability element. It utilizes the EM algorithm to estimate the time-series empirical ZCAPM regression.
- Called by: `ana.m`
- Calls: `ols_estimator.m`, `solve_lineq_v2.m`

```matlab
function coeff=solve_hidden_variable_v2(assets,mu_sigma)
dim=size(assets);
factors=mu_sigma(:,1:2);
num_factor=2;
%%%% ZCAPM regression (EM) %%%%
hat_pt=zeros(dim(1),1);
eta_p=zeros(dim(1),1);
eta_n=zeros(dim(1),1);
coeff=zeros(dim(2),num_factor+1);
for j=1:dim(2)
    X=factors(:,1);
    Y=assets(:,j)-mu_sigma(:,3);
    [beta_hat,rs,t_stat,u_hat]=ols_estimator(X,Y);
    Z=factors;
    for kk=1:dim(1)
        if (u_hat(kk)>=0)
            Z(kk,2)=factors(kk,2);
            hat_pt(kk,1)=1;
        else
            Z(kk,2)=-factors(kk,2);
            hat_pt(kk,1)=0;
        end
    end
    [beta_hat,rs,t_stat,u_hat]=ols_estimator(Z,Y);
    p_0=0;
    for kk=1:dim(1)
        if (hat_pt(kk,1)==1)
            p_0=p_0+hat_pt(kk,1);
        end
    end
    p_0=p_0/dim(1);
    sigma_0=mean(u_hat(:,1).*u_hat(:,1));
    delta=1;
    while (delta>0.001)
        for kk=1:dim(1)
            eta_p(kk,1)=exp(-(Y(kk,1)-beta_hat(1)*factors(kk,1)-beta_hat(2)*factors(kk,2))^2....
                /2/sigma_0);
            eta_n(kk,1)=exp(-(Y(kk,1)-beta_hat(1)*factors(kk,1)+beta_hat(2)*factors(kk,2))^2....
                /2/sigma_0);
            hat_pt(kk,1)=eta_p(kk,1)*p_0/(eta_p(kk,1)*p_0+eta_n(kk,1)*(1-p_0));
        end
        [beta_itr,hat_sigma,p]=solve_lineq_v2(Y,hat_pt,factors);
        diff=[abs((beta_itr(1)-beta_hat(1))/beta_hat(1)),abs((beta_itr(2)-beta_hat(2))/beta_hat(2)),...
            abs((p-p_0)/p_0),abs((hat_sigma-sigma_0)/sigma_0)];
        delta=max(diff);
        p_0=p;
        sigma_0=hat_sigma;
        beta_hat=beta_itr;
    end
    for i=1:num_factor
        coeff(j,i)=beta_hat(i);
    end
    coeff(j,num_factor+1)=p_0;
end
```

## read_factors.m

- Loads the data for asset pricing factors input files into the program. Here the data set `mu_sigma.xlsx` contains both value-weighted market mean return and value-weighted market daily sigma (or cross-sectional return dispersion or RD). Only sigma is stored in factors and used later. The data set `ff_factors_day.xlsx` contains the three factors in the Fama and French three-factor model downloaded from Kenneth French's dataset. The market factor and riskless rate are stored in factors and used later. Our data starts from 1960, but our sample period starts from 1964. Therefore, factors only read rows starting from 1005 or 1006 in the original excel file. Users should change this row number based on their own data sources and structure. The data file must be stored within the same folder as Matlab codes – otherwise, a new path will need to be defined. Variable names appear in the first row of the data set.
- Called by: `ana.m`
- Calls: n/a

```matlab
function factors=read_factors()
filename='mu_sigma.xlsx';
data1 = xlsread(filename);
filename='ff_factors_day.xlsx';
data2 = xlsread(filename);
factors=[data1(1005:end,1),data2(1006:end,2),...
    data1(1005:end,3)*100,data2(1006:end,6)]; %%%% combines the RD (sigma) and market factor together
```

## read_etf_data.m

- Loads data set files of daily stock returns for test asset portfolios into the program. The xlsx files starting with `ff` and `ind47` are data downloaded from Kenneth French's website. Like factor data, all Excel data files need to be stored in the same folder as the codes. Users need to redefine which data and which row that Matlab reads based own their own data structure. Variable names appear in the first row.
- Called by: `ana.m`
- Calls: n/a

```matlab
function [ff25,ind47,own25,bm100,bmop25,bminv25,opinv25]=read_etf_data()
filename='ff25_day_vw.xlsx';
%%%% 25 size-BM portfolios from Kenneth French website
ff25 = xlsread(filename);
ff25=ff25(1006:end,:);
%%%% row (date) that daily returns begin
filename='ind47_day_vw.xlsx'; %%%% 47 industry portfolios from Kenneth French website
ind47 = xlsread(filename);
ind47=ind47(1006:end,:);
filename='beta_zstar_assets.xlsx';
own25 = xlsread(filename);
own25=[own25(:,1),own25(:,2:end)*100]; %%%% 25 beta-zeta portfolios created by the authors
filename='ff_bm_100.xlsx';
bm100 = xlsread(filename);
bm100=bm100(1006:end,:);
filename='ff_bmop_25.xlsx';
bmop25 = xlsread(filename);
bmop25=bmop25(127:end,:);
filename='ff_bminv_25.xlsx';
bminv25 = xlsread(filename);
bminv25=bminv25(127:end,:);
filename='ff_opinv_25.xlsx';
opinv25 = xlsread(filename);
opinv25=opinv25(127:end,:); %%%% other test asset portfolios from Kenneth French website
```

## scan_data_struct.m

- Daily data in Matlab only contains rows instead of calendar date. Because our regression uses daily data within calendar time, this function gets the starting and ending row numbers for each corresponding calendar time. (e.g., rows from 1 to 22 in daily data files are days in January 1964)
- Called by: `ana.m`
- Calls: n/a

```matlab
function [data_nm,data_str]=scan_data_struct(data)
dim=size(data);
data_ini=data(1,1);
data_inf=data_ini;
data_ps=zeros(1000,2);
data_ps(1,1)=1;
count=1;
for i=2:dim(1)
    if (data(i,1)~=data_ini)
        count=count+1;
        data_ps(count-1,2)=i-1;
        data_ps(count,1)=i;
        temp=[data_inf;data(i,1)];
        data_ini=data(i,1);
        data_inf=temp;
    end
end
data_ps(count,2)=dim(1);
data_str=data_ps(1:count,:);
data_nm=data_inf;
```

## gen_cul_ret.m

- Compounding daily returns to get monthly returns. For each out-of-sample month, the monthly return is calculated by compounding all daily returns within the month.
- Called by: `ana.m`
- Calls: n/a

```matlab
function cul_ret=gen_cul_ret(data)
dim=size(data);
cul_ret=zeros(dim(1),dim(2));
for i=1:dim(1)
    if (i>=2)
        cul_ret(i,:)=(1+data(i,:)/100).*(1+cul_ret(i-1,:))-1;
    else
        cul_ret(i,:)=data(i,:)/100;
    end
end
cul_ret=cul_ret*100;
```

## solve_lineq_v2.m

- Solves linear equations for the empirical ZCAPM.
- Called by: `solve_hidden_variable_v2.m`
- Calls: n/a

```matlab
function [hat_beta,hat_sigma,p]=solve_lineq_v2(Y,hat_pt,factors)
dim=size(Y);
a=zeros(2,2);
b=zeros(2,1);
hat_dt=2*hat_pt-1;
a(1,1)=sum(factors(:,1).*factors(:,1));
a(1,2)=sum(hat_dt(:,1).*factors(:,1).*factors(:,2));
a(2,1)=sum(hat_dt(:,1).*factors(:,1).*factors(:,2));
a(2,2)=sum(factors(:,2).*factors(:,2));
b(1,1)=sum(Y(:,1).*factors(:,1));
b(2,1)=sum(hat_dt(:,1).*Y(:,1).*factors(:,2));
hat_beta=linsolve(a,b);
p=mean(hat_pt(:,1));
sigma_t=zeros(dim(1),1);
for i=1:dim(1)
    sigma_t(i,1)=(Y(i,1)-hat_beta(1,1)*factors(i,1))^2 ...
        -2*(Y(i,1)-hat_beta(1,1)*factors(i,1))* ...
        hat_beta(2,1)*hat_dt(i,1)*factors(i,2)...
        +hat_beta(2,1)^2*factors(i,2)^2;
end
hat_sigma=mean(sigma_t(:,1));
```
