# Pocket Financial Tracker - User Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Build](#build)
3. [Getting Started](#getting-started)
4. [Main Features](#main-features)
5. [User Interface Guide](#user-interface-guide)
6. [Financial Calculations](#financial-calculations)
7. [Tips and Best Practices](#tips-and-best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Technical Information](#technical-information)

## Introduction

Pocket Financial Tracker is a minimalistic application designed to help you manage your daily finances. It features a 30-day calendar view that calculates how much money you can spend each day based on your income, savings goals, and spending habits.

The application is designed with simplicity in mind, focusing on the essential features needed for effective daily financial management without overwhelming you with complex options.

## Build

To build the application on your platform:

1. Ensure Python is installed on your system
2. Install PyInstaller: `pip install pyinstaller`
3. Download and extract the source code (`financial_tracker_source.zip`)
4. Navigate to the extracted directory in your terminal/command prompt
5. Run the following command:
   ```
   pyinstaller --onefile --windowed --name FinancialTracker --hidden-import tkinter main.py
   ```
6. The executable will be created in the `dist` folder
7. Run the application by double-clicking the executable file

## Getting Started

When you first launch Pocket Financial Tracker, you'll see a calendar view on the left and control panels on the right. Here's how to get started:

1. **Set Your Payday**: Click on the date in the calendar that corresponds to your payday
2. **Add Income**: Enter your income amount in the "Amount" field and click "Add Income"
3. **Set Savings Goal**: In the Settings section, choose either:
   - Save % (percentage of income to save)
   - Fixed Limit $ (fixed daily spending limit)
4. **Enter the value** and click "Save Settings"
5. **Track Daily Expenses**: As you spend money, select the date and add expenses

The application will automatically calculate your daily spending limits and adjust them based on your actual spending.

## Main Features

### 30-Day Calendar View
- Visual representation of the current month
- Color-coded days to indicate financial status
- Easy date selection for viewing and entering transactions

### Daily Spending Limit Calculation
- Automatic calculation based on income and savings goals
- Dynamic adjustment based on actual spending
- Rollover of unspent funds to the next day

### Transaction Management
- Record income and expenses with descriptions
- View transaction history for each day
- Track daily spending against limits

### Savings Goals
- Set percentage-based savings goals
- Alternatively, set fixed daily spending limits
- Automatic recalculation when settings change

### Data Persistence
- Automatic saving of all transactions and settings
- Data loaded automatically when the application starts

## User Interface Guide

### Calendar Section (Left)
- **Month Navigation**: Use the < and > buttons to move between months
- **Date Selection**: Click on any day to select it and view/edit its transactions
- **Day Display**: Days with financial data are highlighted

### Details Section (Top Right)
- **Selected Date**: Shows the currently selected date
- **Daily Limit**: Displays the calculated spending limit for the selected day
- **Spent Today**: Shows the total amount spent on the selected day
- **Remaining Today**: Displays the remaining amount available to spend

### Transactions Section (Middle Right)
- Lists all transactions for the selected date
- Format: +/-$Amount (type): description

### Add Transaction Section (Bottom Right)
- **Amount**: Enter the transaction amount
- **Description**: Add an optional description
- **Add Income/Expense Buttons**: Record the transaction

### Settings Section (Bottom)
- **Save %**: Set a percentage of income to save
- **Fixed Limit $**: Set a fixed daily spending limit
- **Save Settings Button**: Apply the selected settings

## Financial Calculations

### Daily Limit Calculation
When using percentage-based savings:
1. Total available amount = Income - (Income × Savings %)
2. Daily limit = Available amount ÷ Days until next payday

When using fixed daily limit:
- The daily limit is simply the amount you specified

### Rollover/Deficit Logic
- **If you spend less than your daily limit**: The unspent amount is added to the next day's limit
  - Example: If your limit is $26 and you spend $20, the next day's limit will be $26 + $6 = $32

- **If you spend more than your daily limit**: The excess is subtracted from the next day's limit
  - Example: If your limit is $26 and you spend $30, the next day's limit will be $26 - ($30 - $26) = $22

## Tips and Best Practices

### Setting Effective Savings Goals
- Start with a modest savings percentage (10-15%) and adjust as needed
- Consider your fixed expenses when setting daily limits
- Adjust your savings goals for months with unusual expenses

### Daily Financial Management
- Enter expenses as they occur to maintain accurate daily limits
- Review your spending patterns at the end of each week
- Adjust your savings goals or daily limits based on your financial progress

### Long-term Planning
- Use the application to experiment with different savings percentages
- Track how changes in income affect your daily spending capacity
- Identify spending patterns to optimize your financial habits

## Troubleshooting

### Application Won't Start
- Ensure you have the correct version for your operating system
- For Linux: Check that the file is executable (`chmod +x FinancialTracker`)
- For custom builds: Ensure Python and Tkinter are properly installed

### Data Issues
- If the application behaves unexpectedly, check the data.json file for corruption
- Back up your data.json file regularly to prevent data loss

### Display Problems
- If the calendar doesn't display correctly, try resizing the application window
- Ensure your system's display scaling settings are at 100%

## Technical Information

### Application Architecture
- **logic.py**: Contains the core financial calculation logic
- **main.py**: Implements the user interface using Tkinter
- **data.json**: Stores all transaction and settings data

### Data Storage
All data is stored in a JSON file with the following structure:
- **settings**: Contains savings percentage and fixed daily limit
- **transactions**: Stores all transactions organized by date
- **daily_limits**: Calculated daily limits for each date

### Customization
Advanced users can modify the source code to:
- Change the calendar display
- Add additional financial calculations
- Implement new features like expense categories or reports

For any technical questions or feature requests, please contact the developer.
