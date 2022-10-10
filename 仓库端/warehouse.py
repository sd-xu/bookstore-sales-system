import pandas as pd
from xmlrpc.server import SimpleXMLRPCServer
import csv
import numpy as np
from threading import Thread

csv_path = './warehouse.csv'

class Warehouse:
    def __init__(self):
        self.alarm = False

    def buyonekind(self,bookname, kind, number):
        """
        尝试购买书籍
        返回购买情况
        """
        warehouse_book = pd.read_csv('Warehouse\\book_Jul.csv', encoding='gb2312')
        for i in warehouse_book.index.tolist():
            if warehouse_book["书籍名称"][i] == bookname and warehouse_book["书籍类别"][i] == kind:
                if warehouse_book["库存"][i] < number:
                    return "库存不足", 2
                return warehouse_book.loc[i].to_dict(),0

        return "查无此书",1

    def buy(self, order_list):
        warehouse_book = pd.read_csv('Warehouse\\book_Jul.csv', encoding='gb2312')
        for order in order_list:
            row_index = warehouse_book[(warehouse_book.书籍类别 == order[0]) &
                                       (warehouse_book.书籍名称 == order[1])].index.tolist()[0]  # 书籍对应的行索引
            warehouse_book.loc[row_index, "库存"] -= order[3]  # 这里默认客户端下单前已经完成购买数量 ≤ 库存数量的判断 !
            warehouse_book.loc[row_index, "销售数量"] += order[3]

        with open('Warehouse\\need.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            row_index_all = warehouse_book.index.tolist()
            for row in row_index_all:
                if warehouse_book["库存"][row] < 100:
                    data = [warehouse_book["书籍类别"][row], warehouse_book["书籍名称"][row], "1000"]
                    writer.writerow(data)

        with open('Warehouse\\need.csv', 'rb') as f:
            cnt = 0
            for line in f:
                cnt += 1
            if cnt >= 10:
                self.alarm = True

        warehouse_book.to_csv('Warehouse\\book_Jul.csv', index=False, encoding='gb2312')

    def returnBookInfo(self):
        book_Jul = pd.read_csv('Warehouse\\book_Jul.csv', encoding='gb2312')
        return book_Jul.to_json()

    def retriveAll(self):
        """
        检索所有书籍
        返回书籍表
        """
        # discounted_book = pd.read_csv('Discounted_Book_Info\\discounted_book_Jul.csv', encoding='gb2312')  # 7月特价书籍
        # del discounted_book["进价"]
        # del discounted_book["销售数量"]
        # return pd.read_csv('Discounted_Book_Info\\discounted_book_Jul.csv', encoding='gb2312').to_json()
        booklist = np.array(pd.read_csv('Warehouse\\book_Jul.csv', encoding='gb2312'))
        allbook = "书籍类别    书籍名称                                 售价      库存\n"
        for i in range(len(booklist)):
            if str(booklist[i][0]) != "nan":
                allbook += str(booklist[i][0]).ljust(10, ' ') + str(booklist[i][1]).ljust(35, ' ') + ' ' + (
                            str(booklist[i][3]) + "元").ljust(8, ' ') + (str(int(booklist[i][4])) + "本").ljust(8,
                                                                                                              ' ') + "\n"
        return allbook

    def retrive(self,bookname):
        """
        检索所有书籍
        返回书籍表
        """
        # discounted_book = pd.read_csv('Discounted_Book_Info\\discounted_book_Jul.csv', encoding='gb2312')  # 7月特价书籍
        # del discounted_book["进价"]
        # del discounted_book["销售数量"]
        # return str(discounted_book)
        booklist = np.array(pd.read_csv('Warehouse\\book_Jul.csv', encoding='gb2312'))
        allbook = "书籍类别    书籍名称                                 售价      库存\n"
        find = False
        for i in range(len(booklist)):
            if str(booklist[i][1]) == bookname:
                find = True
                allbook += str(booklist[i][0]).ljust(10, ' ') + str(booklist[i][1]).ljust(35, ' ') + ' ' + (
                            str(booklist[i][3]) + "元").ljust(8, ' ') + (str(int(booklist[i][4])) + "本").ljust(8,
                                                                                                              ' ') + "\n"
        if find:
            return allbook
        else:
            return "查无此书"


    def update_discount_price(self, discounted_book): # DataFrame
        warehouse_book = pd.read_csv('Book_Info\\book_Jul.csv', encoding='gb2312') # 7月书单
        discounted_book_index = discounted_book.index.tolist() # 索引列表
        # 特价书籍售价更新, 注意是下月的售价
        for i in discounted_book_index:
            row_index = warehouse_book[(warehouse_book.书籍类别 == discounted_book["书籍类别"][i]) &
                                       (warehouse_book.书籍名称 == discounted_book["书籍名称"][i])].index.tolist()[0]  # 书籍对应的行索引
            if warehouse_book["售价"][row_index] * 0.9 >= warehouse_book["进价"][row_index]:
                warehouse_book["售价"][row_index] *= 0.9
            else:
                warehouse_book["售价"][row_index] = warehouse_book["进价"][row_index]
        warehouse_book.to_csv('Warehouse\\book_Jul.csv', index=False, encoding='gb2312')

    def get_purchase_order(self): # return purchase_order(DataFrame), alarm(Bool)
        re = self.alarm
        need_book = None
        if self.alarm:
            need_book = pd.read_csv('Warehouse\\need.csv', encoding='gb2312')
            pd.DataFrame(columns=["书籍类别","书籍名称","采购数量"]).to_csv('Warehouse\\need.csv', index=False, encoding='gb2312')
            self.alarm = False
        return need_book,re


if __name__ == '__main__':

    t = Thread()
    def service():
        with SimpleXMLRPCServer(('127.0.0.1', 8002),allow_none=True) as server:
            server.register_instance(Warehouse())
            server.serve_forever()
    t.run = service
    t.start()

    while True:
        s = input('[1] 修改进价 [0] 退出\n')
        if s == '1':
            f = input('输入书籍名称：')
            k = input('输入书籍类型：')
            warehouse_book = pd.read_csv('Warehouse\\book_Jul.csv', encoding='gb2312')
            mark = True
            for i in warehouse_book.index.tolist():
                if warehouse_book["书籍名称"][i] == f and warehouse_book["书籍类别"][i] == k:
                    mark = False
                    try:
                        n = float(input('输入新进价：'))
                        if n <= 0:
                            raise Exception()
                        warehouse_book.loc[i, "进价"] = n
                        
                        warehouse_book.loc[i, "售价"] = n + int(n*0.25)
                        warehouse_book.to_csv('Warehouse\\book_Jul.csv', index=False, encoding='gb2312')
                    except Exception as e:
                        print(e)
                        print('格式不正确')
                    break
            if mark:
                print('未找到书籍')
        elif s == '0':
            break


