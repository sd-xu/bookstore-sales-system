from socket import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import csv
import os
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
from threading import Thread

class Bookstore(object):

    def __init__(self, warehouse):
        self.warehouse = warehouse

    # 客户注册
    def client_register(self, name, ID, password):
        client_list = os.listdir('Client_Account_Info')
        if name + '.csv' in client_list:
            return False

        datas = [["name", "ID", "password"], [name, ID, password]] # 第一个列表元素表示 CSV 文件标题
        with open('Client_Account_Info\\' + name + '.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for row in datas:
                writer.writerow(row)
        return True

    # 客户登录
    def client_login(self, name, ID, password):
        client_list = os.listdir('Client_Account_Info')
        if name + '.csv' not in client_list:
            return 1 # 用户名不存在
        account = pd.read_csv('Client_Account_Info\\' + name + '.csv', encoding='gb2312')
        if str(account['ID'][0]) != ID:
            return 2 # 账号不正确
        if str(account['password'][0]) != password:
            return 3 # 密码不正确
        return 0 # 登录成功

    # 客户下单
    def client_purchase(self, client_name, order_list): # order_list:列表, order:列表(对应每书)
        print(order_list)
        # 用户购买信息更新
        client_purchase_list = os.listdir('Client_Purchase_Info')
        print(client_purchase_list)
        with open('Client_Purchase_Info\\' + client_name + '_purchase.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            if client_name + '_purchase.csv' not in client_purchase_list:
                writer.writerow(["书籍类别", "书籍名称", "书籍单价", "购买数量", "书籍总价"])
            for order in order_list:
                writer.writerow(order)

        # 销售信息更新
        sales_Jul = pd.read_csv('Sales_Info\\sales_Jul.csv', encoding='gb2312')
        self.update_book_price()
        book_Jul = pd.read_csv('Book_Info\\book_Jul.csv', encoding='gb2312') # 7月书单
        for order in order_list: # 7月
            # 月度销售信息更新
            category_index = sales_Jul[sales_Jul.书籍类别 == order[0]].index.tolist()[0] # 书类对应的行索引
            sales_Jul.loc[category_index,"销售数量"] +=  order[3] # 哪类书卖了几本
            sales_Jul.loc[category_index,"销售额"] += order[4]
            row_index = book_Jul[(book_Jul.书籍类别 == order[0]) &
                                 (book_Jul.书籍名称 == order[1])].index.tolist()[0]  # 书籍对应的行索引
            cost = float(book_Jul["进价"][row_index]) * order[3]           # 书籍总进价 = 书籍进价 * 数量
            sales_Jul.loc[category_index,"销售总利润"] = order[4] - cost # 销售利润 += 书籍总价 - 书籍总进价

            # 书单信息更新
            book_Jul.loc[row_index,"库存"] -= order[3] # 这里默认客户端下单前已经完成购买数量 ≤ 库存数量的判断 !
            book_Jul.loc[row_index,"销售数量"] += order[3]

        sales_Jul.to_csv('Sales_Info\\sales_Jul.csv', index=False, encoding='gb2312')
        book_Jul.to_csv('Book_Info\\book_Jul.csv', index=False, encoding='gb2312')

    # 当月特价书籍
    def client_get_discounted_book(self):
        discounted_book = pd.read_csv('Discounted_Book_Info\\discounted_book_Jul.csv', encoding='gb2312') # 7月特价书籍
        del discounted_book["进价"]
        del discounted_book["销售数量"]
        return str(discounted_book)

    # 下月特价书籍
    def next_month_discounted_book(self):
        self.update_book_price()
        book_Jul = pd.read_csv('Book_Info\\book_Jul.csv', encoding='gb2312') # 7月书单
        discounted_book = book_Jul.sort_values(by='销售数量')[0:10] # 销量倒数十本
        discounted_book_index = discounted_book.index.tolist() # 索引列表
        # 特价书籍售价更新, 注意是下月的售价
        for i in discounted_book_index:
            if discounted_book["售价"][i] * 0.9 >= discounted_book["进价"][i]:
                discounted_book["售价"][i] *= 0.9
            else:
                discounted_book["售价"][i] = discounted_book["进价"][i]
        print(discounted_book)
        discounted_book.to_csv('Discounted_Book_Info\\discounted_book_Aug.csv', index=False, encoding='gb2312')

        # 更新特价书籍售价（仓库端）
        self.warehouse.update_discount_price(discounted_book)

    # 统计每年销售情况
    def annual_sales(self):
        mpl.rcParams["font.sans-serif"] = ["SimHei"]
        sales_2022 = pd.read_csv('Sales_Info\\sales_2022.csv', encoding='gb2312')

        ax1 = plt.subplot(2, 2, 1)
        x = ["杂志", "文化、社会", "摄影", "广告", "艺术", "文学"]
        y = []
        for i in range(6):
            y.append(sales_2022[x[i]].sum())
        plt.bar(x, y, color='pink', label='销售数量')
        for i in range(6):
            plt.text(x[i], y[i], '%d' % y[i], ha='center', va='bottom')
        plt.legend(loc='best')
        plt.title('各类书年销售数量')

        ax2 = plt.subplot(2, 2, 2)
        sales_2022["销售额"].plot(kind="pie", figsize=(6, 6), autopct='%3.2f%%')
        sum = sales_2022["销售额"].sum()
        plt.title('年销售额 = ' + str(sum))

        ax3 = plt.subplot(2, 2, 3)
        labels = ["杂志", "文化、社会", "摄影", "广告", "艺术", "文学"]
        bar_width = 0.35
        y_2021 = [60000, 428124, 6000, 82680, 90504, 308136]
        plt.bar(np.arange(6) - 0.5 * bar_width, y_2021, label='2021年', width=bar_width, color='b')
        plt.bar(np.arange(6) + 0.5 * bar_width, y, label='2022年', width=bar_width, color='pink')

        plt.xticks(np.arange(6), labels)
        plt.xlabel('书籍类别')
        plt.ylabel('销售数量')
        plt.title('销售趋势')
        plt.legend()

        ax4 = plt.subplot(2, 2, 4)
        sales_2022["销售总利润"].plot(kind="pie", figsize=(6, 6), autopct='%3.2f%%')
        sum = sales_2022["销售总利润"].sum()
        plt.title('年销售总利润 = ' + str(sum))

        plt.show()

    # 统计每季度销售情况
    def quartery_sales(self):
        mpl.rcParams["font.sans-serif"] = ["SimHei"]
        sales_Jul = pd.read_csv('Sales_Info\\sales_Jul.csv', index_col="书籍类别", encoding='gb2312')
        sales_Jun = pd.read_csv('Sales_Info\\sales_Jun.csv', index_col="书籍类别", encoding='gb2312')
        y_May = [6000, 42812, 600, 8268, 9050, 30814]

        ax1 = plt.subplot(2, 2, 1)
        x = sales_Jul.index
        y_Jul = list(sales_Jul.销售数量.values)
        y_Jun = list(sales_Jun.销售数量.values)
        y = []
        for i in range(6):
            y.append(y_Jul[i] + y_Jun[i] + y_May[i])
        plt.bar(x, y, color='pink', label='销售数量')
        for i in range(6):
            plt.text(x[i], y[i], '%d' % y[i], ha='center', va='bottom')
        plt.legend(loc='best')
        plt.title('各类书季销售数量')

        ax2 = plt.subplot(2, 2, 2)
        x_ax2 = [5472985.32, 4560821.1, 3674034.3, 0]
        y_ax2 = ["5月", "6月", "7月", "8月"]
        plt.pie(x_ax2, labels=y_ax2, autopct='%3.2f%%')
        sum = 13707840.72
        plt.title('季销售额 = ' + str(sum))

        ax3 = plt.subplot(2, 2, 3)
        labels = sales_Jul.index
        bar_width = 0.35
        y_ax3 = [17000, 121301, 1700, 23426, 25643, 87305]
        plt.bar(np.arange(6) - 0.5 * bar_width, y_ax3, label='第一季度', width=bar_width, color='b')
        plt.bar(np.arange(6) + 0.5 * bar_width, y, label='第二季度', width=bar_width, color='pink')

        plt.xticks(np.arange(6), labels)
        plt.xlabel('书籍类别')
        plt.ylabel('销售数量')
        plt.title('销售趋势')
        plt.legend()

        ax4 = plt.subplot(2, 2, 4)
        x_ax4 = [3822601.32, 3185501.1, 2567809.2, 0]
        y_ax4 = ["5月", "6月", "7月", "8月"]
        plt.pie(x_ax4, labels=y_ax4, autopct='%3.2f%%')
        sum = 9575911.62
        plt.title('季销售总利润 = ' + str(sum))

        plt.show()

    # 统计每月销售情况
    def monthly_sales(self):
        mpl.rcParams["font.sans-serif"]=["SimHei"]
        sales_Jul = pd.read_csv('Sales_Info\\sales_Jul.csv', index_col="书籍类别", encoding='gb2312')
        sales_Jun = pd.read_csv('Sales_Info\\sales_Jun.csv', index_col="书籍类别", encoding='gb2312')

        ax1 = plt.subplot(2, 2, 1)
        x = sales_Jul.index
        y = list(sales_Jul.销售数量.values)
        plt.bar(x, y, color='pink', label='销售数量')
        for i in range(6):
            plt.text(x[i], y[i], '%d'%y[i], ha='center', va='bottom')
        plt.legend(loc='best')
        plt.title('各类书月销售数量')

        ax2 = plt.subplot(2, 2, 2)
        sales_Jul["销售额"].plot(kind="pie", figsize=(6, 6), autopct='%3.2f%%')
        sum = sales_Jul["销售额"].sum()
        plt.title('月销售额 = ' + str(sum))

        ax3 = plt.subplot(2, 2, 3)
        labels = sales_Jul.index
        bar_width = 0.35
        y_Jun = list(sales_Jun.销售数量.values)
        plt.bar(np.arange(7) - 0.5 * bar_width, y_Jun, label='六月', width=bar_width, color='b')
        plt.bar(np.arange(6) + 0.5 * bar_width, y, label='七月', width=bar_width, color='pink')

        plt.xticks(np.arange(6), labels)
        plt.xlabel('书籍类别')
        plt.ylabel('销售数量')
        plt.title('销售趋势')
        plt.legend()

        ax4 = plt.subplot(2, 2, 4)
        sales_Jul["销售总利润"].plot(kind="pie", figsize=(6, 6), autopct='%3.2f%%')
        sum = sales_Jul["销售总利润"].sum()
        plt.title('月销售总利润 = ' + str(sum))

        plt.show()

    # 更新库存清单
    def update_book_price(self):
        book_Jul = pd.read_json(self.warehouse.returnBookInfo())
        book_Jul.to_csv('Book_Info\\book_Jul.csv', index=False, encoding='gb2312')

    # 获取警报和采购单
    def get_purchase_order(self):
        purchase_order, alarm = self.warehouse.get_purchase_order()
        if alarm:
            purchase_order.to_csv('Purchase_Order_Info\\purchase_order.csv', index=False, encoding='gb2312')
            print("警告！库存出现短缺")
        else:
            print("暂无采购单")

if __name__ == '__main__':
    warehouse = xmlrpc.client.ServerProxy("http://127.0.0.1:8002")
    bookstore = Bookstore(warehouse)

    t = Thread()
    def service():
        with SimpleXMLRPCServer(('127.0.0.1', 8001),allow_none=True) as server:
            server.register_instance(Bookstore(warehouse))
            server.serve_forever()
    t.run = service
    t.start()

    while True:
        #服务模块
        while True:
            choice = input("请选择您需要的服务 \n"
                           "1.统计每月的销售情况\n"
                           "2.统计每季度的销售情况\n"
                           "3.统计每年的销售情况\n"
                           "4.统计当月销售数量排名后十位的书籍(特价书籍)\n"
                           "5.获取警报和采购单\n"
                           "6.退出\n")
            if choice == '1': bookstore.monthly_sales()
            elif choice == '2': bookstore.quartery_sales()
            elif choice == '3': bookstore.annual_sales()
            elif choice == '4': bookstore.next_month_discounted_book()
            elif choice == '5': bookstore.get_purchase_order()
            elif choice == '6': break
            else : print("输入不符合规范，请重新输入\n\n\n")