# Equilibriumn Valuation Analysis
# Justin Dano
if (!require("DT")) install.packages('DT')
if (!require("plyr")) install.packages('plyr')
if (!require("gridExtra")) install.packages('gridExtra')
if (!require("ggplot")) install.packages('ggplot', repos = "http://cran.us.r-project.org")
if (!require("ggplot2")) install.packages('ggplot2')
if (!require("MASS2")) install.packages('MASS')
library(DT)
library(plyr)
library(ggplot2)
library(gridExtra)
library(glmnet)
library(data.table) 

get_data <- function(path) {
  setwd(path)
  companies <- c('amazon', 'apple', 'boeing', 'coke', 'comcast', 'exxon', 'ibm', 'netflix', 'pg')
  file_ext <- "\\model.csv"
  regression_data <- list()
  for (i in seq_along(companies)) {
    file_name <- paste("data\\", companies[i], file_ext, sep="")
    df <- read.csv(file=file_name, header=TRUE, row.names=1)
    regression_data[[i]] <- df
  }
  names(regression_data) <- companies
  return(regression_data) 
}

clean_stock_data <- function(df) {
  df <- df[df$REVENUE != 0, ]
  df <- df[complete.cases(df),]
  df$DATE <- rownames(df)
  df$DATE <- as.Date(df$DATE, "%Y-%m-%d")
  return (df)
}

clean_data <- function(data) {
  cleaned_list <- list()
  for (stock in names(data)) {
    cleaned_list[[stock]] <- clean_stock_data(data[[stock]])
  }
  return (cleaned_list)
}

gen_plot <- function(company, feature, company_name) {
  stock_data <- company
  
  splot <- ggplot( data = stock_data, aes( DATE, stock_data[,feature], group=1 ), environment = environment()) + 
    geom_point() + ylab(feature)+  ggtitle(company_name)
  
  return(splot)
}

display_all_metrics <- function(company, feature) {
  pl <- list()
  for (stock in names(company)) {
    pl[[stock]] <- gen_plot(company[[stock]], feature, stock)
  }
  grid.arrange(pl$apple, pl$amazon, pl$boeing, pl$coke, pl$comcast, pl$exxon, pl$ibm, pl$netflix, pl$pg)
  
}

display_outliers <- function(orig, capped, removed, company, feature) {
  orig_stock_df <- orig[[company]]
  capped_stock_df <- capped[[company]]
  removed_stock_df <- removed[[company]]
  o_s_df <- orig_stock_df[names(orig_stock_df) %in% c("DATE", feature)]
  c_s_df <- capped_stock_df[names(capped_stock_df) %in% c("DATE", feature)]
  r_s_df <- removed_stock_df[names(removed_stock_df) %in% c("DATE", feature)]
  o_s_df$outlier <- "Original"
  c_s_df$outlier <- "Capped"
  r_s_df$outlier <- "Removed"
  merged_df <- rbind(o_s_df, c_s_df, r_s_df)
  merged_df$outlier <- factor(merged_df$outlier, levels=c("Original", "Capped", "Removed"))
  plt <- ggplot( data = merged_df, aes( DATE, merged_df[, feature])) + geom_point() + ggtitle(company) + ylab(feature)
  plt + facet_grid(outlier ~ .)
  
}

remove_outliers <- function(stock_df, cols) {
  for (i in names(stock_df)) {
    if (i %in% cols) {
      metric <- stock_df[[i]]
      qnt <- quantile(metric, probs=c(.25, .75), na.rm = T)
      caps <- quantile(metric, probs=c(.05, .95), na.rm = T)
      H <- 1.5 * IQR(metric, na.rm = T)
      metric[metric < (qnt[1] - H)] <- NA
      metric[metric > (qnt[2] + H)] <- NA
      stock_df[[i]] <- metric
      stock_df <- na.omit(stock_df)
    }
  }
  #stock_df <- na.omit(stock_df)
  return (stock_df)
}

cap_outliers <- function(stock_df, cols) {
  for (i in names(stock_df)) {
    if (i %in% cols) {
      metric <- stock_df[[i]]
      qnt <- quantile(metric, probs=c(.25, .75), na.rm = T)
      caps <- quantile(metric, probs=c(.05, .95), na.rm = T)
      H <- 1.5 * IQR(metric, na.rm = T)
      metric[metric < (qnt[1] - H)] <- caps[1]
      metric[metric > (qnt[2] + H)] <- caps[2]
      #print(setdiff(stock_df[[i]], metric))
      stock_df[[i]] <- metric
    }
  }
  return (stock_df)
}

process_outliers <- function(stocks_df, option) {
  cols <- c("REVENUE","EBITDA_MARGIN","TAX_EXPENSE_MARGIN", "
          CAPEX_MARGIN", "CHNG_WC_MARGIN", "REVENUE_GROWTH", 
            "EBITDA_GROWTH", "CAPEX_GROWTH", "FIRM_VALUE", 
            "NON_OP_ASSETS", "WADS", "PRICE")
  
  equity_data <- list()
  
  for (i in names(stocks_df)) {
    if (option == 1) {
      s_df <- stocks_df[[i]]
    } else if (option == 2) {
      s_df<- remove_outliers(stocks_df[[i]], cols)
    } else {
      s_df <- cap_outliers(stocks_df[[i]], cols)
    }
    #s_df$DATE <-  rownames(s_df)
    equity_data[[i]] <- s_df
  }
  return (equity_data)
}

compare_outliers <- function(df_orig, df_updated) {
  g1 <- ggplot( data = df_orig, aes( DATE, EBITDA_MARGIN, group=1 ), environment = environment()) + 
    geom_point() + ylab("feature")+  ggtitle("df_orig")
  
  g2 <- ggplot( data = df_updated, aes( DATE, EBITDA_MARGIN, group=1 ), environment = environment()) + 
    geom_point() + ylab("feature")+  ggtitle("df_updated")
  
  grid.arrange(g1, g2)
}

combine_data <- function(list_of_dataframes) {
  return(ldply(list_of_dataframes, data.frame, .id="company"))
}

display_data <- function(data) {
  datatable(data, extensions = 'AutoFill', options = list(autoFill = TRUE))
}

display_company_metrics <- function(data) {
  par(mfrow=c(3, 4))  # divide graph area in 2 columns
  
  scatter.smooth(x=data$DATE, y=data$REVENUE, main="REVENUE")
  scatter.smooth(x=data$DATE, y=data$EBITDA_MARGIN, main="EBITDA_MARGIN") 
  scatter.smooth(x=data$DATE, y=data$CAPEX_MARGIN, main="CAPEX_MARGIN") 
  scatter.smooth(x=data$DATE, y=data$TAX_EXPENSE_MARGIN, main="TAX_EXPENSE_MARGIN") 
  scatter.smooth(x=data$DATE, y=data$FIRM_VALUE, main="REVENUE_GROWTH") 
  scatter.smooth(x=data$DATE, y=data$EBITDA_GROWTH, main="EBITDA_GROWTH") 
  scatter.smooth(x=data$DATE, y=data$CAPEX_GROWTH, main="CAPEX_GROWTH") 
  scatter.smooth(x=data$DATE, y=data$CHNG_WC_MARGIN, main="CHNG_WC_MARGIN")
  scatter.smooth(x=data$DATE, y=data$TB3m, main="TB3M")
  scatter.smooth(x=data$DATE, y=data$TB10YR, main="TB10YR")
  scatter.smooth(x=data$DATE, y=data$PRICE, main="PRICE")
  scatter.smooth(x=data$DATE, y=data$FIRM_VALUE, main="FIRM_VALUE") 
}

main <- function() {
  my_path <- "C:\\Users\\Justin\\Desktop\\FE541\\equilibrium"
  model_data <- get_data()
  cleaned_model_data <- clean_data(model_data)
  #display_all_metrics(cleaned_model_data, 'REVENUE')
  
  test_data <- process_outliers(cleaned_model_data, 3)
  df <- ldply(test_data, data.frame)
  
  # LINEAR REGRESSION
  model <- lm(df$FIRM_VALUE ~ df$REVENUE + df$EBITDA_MARGIN + df$TAX_EXPENSE_MARGIN + 
                df$CAPEX_MARGIN + df$CHNG_WC_MARGIN + df$REVENUE_GROWTH + 
                df$EBITDA_GROWTH + df$CAPEX_GROWTH + df$TB3M + df$TB10YR)
  summary(model)
  layout(matrix(c(1,2,3,4),2,2))
  plot(model)
  
  
  # Prepare data for Ridge/Lasso Regression
  df2 <- df
  # Extact Target as a Vector
  firm_value <- df2[, "FIRM_VALUE"]
  drop_cols <- c("FIRM_VALUE", "WADS", "PRICE", "DATE", ".id")
  df2 <- df2[ , !(names(df2) %in% drop_cols)]
  
  df_matrix <- as.matrix(df2)
  # remove any values non-normal values like NaN
  df_matrix <- df_matrix[!rowSums(!is.finite(df_matrix)),]

  # RIDGE REGRESSION
  set.seed(123)
  ridge_model <- cv.glmnet(df_matrix, firm_value, lambda=10^seq(4, -1, -.1), alpha=0)
  best_ridge_lambda <- ridge_model$lambda.1se
  ridge_coef <- ridge_model$glmnet.fit$beta[, ridge_model$glmnet.fit$lambda == best_ridge_lambda]
  
  # LASSO REGRRSSION
  set.seed(123)
  lasso_model <- cv.glmnet(df_matrix, firm_value, lambda=10^seq(4, -1, -.1), alpha=1)
  # Lambda that gives the best error
  best_lasso_lambda <- lasso_model$lambda.1se
  lasso_coef <- lasso_model$glmnet.fit$beta[, lasso_model$glmnet.fit$lambda == best_lasso_lambda]
  
  # ELASTIC-NET
  set.seed(123)
  elastic_net <- cv.glmnet(df_matrix, firm_value, lambda=10^seq(4, -1, -.1), alpha=0.3)
  best_en_lambda <- elastic_net$lambda.1se
  net_coef <- elastic_net$glmnet.fit$beta[, elastic_net$glmnet.fit$lambda == best_en_lambda]
  
  
  coef <- data.table(lasso = lasso_coef, 
                     elastic_net = net_coef,
                     ridge = ridge_coef)
  
  coef[, feature := names(ridge_coef)]
  coef_plot = melt(coef, id.vars='feature', variable.name='model', value.name='coefficient')
  
  ggplot(coef_plot, aes(x=feature, y=coefficient, fill=model)) + coord_flip() + 
    geom_bar(stat='identity') + facet_wrap( ~ model) + guides(fill=FALSE)
  
  # Price Factors 
  ggplot(coef_plot[!grepl(paste(c('GROWTH','TB'),collapse="|"), feature),], aes(x=feature, y=coefficient, fill=model)) + coord_flip() + 
    geom_bar(stat='identity') + facet_wrap( ~ model) + guides(fill=FALSE)

  # Growth Factors
  ggplot(coef_plot[grepl('GROWTH', feature),], aes(x=feature, y=coefficient, fill=model)) + coord_flip() + 
    geom_bar(stat='identity') + facet_wrap( ~ model) + guides(fill=FALSE)
    
  # Risk-free Rate Factors
  ggplot(coef_plot[grepl('TB', feature),], aes(x=feature, y=coefficient, fill=model)) + coord_flip() + 
    geom_bar(stat='identity') + facet_wrap( ~ model) + guides(fill=FALSE)

  
}

