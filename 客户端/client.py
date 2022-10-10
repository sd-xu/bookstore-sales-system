from socket import *
import pandas as pd
from pandas import DataFrame
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

class Client(object):

    def __init__(self, warehouse,bookstore):
        self.warehouse = warehouse
        self.bookstore = bookstore
        self.purchase = []
        self.allmoney = 0

    def register(self):
        print("开始注册")
        self.name = input('请输入用户名: ')
        self.account = input("请输入账号: ")
        self.password = input('请输入密码: ')

        if self.bookstore.client_register(self.name, self.account, self.password ):
            print("注册成功")
        else:
            print("注册失败")

    def signin(self):
        print("开始登录")
        self.name = input('请输入用户名: ')
        self.account = input("请输入账号: ")
        self.password  = input('请输入密码: ')
        #登录报文
        situaction = self.bookstore.client_login(self.name, self.account, self.password )
        if situaction == 1:
            print("用户名不存在")
        elif situaction == 2:
            print("账号不正确")
        elif situaction == 3:
            print("密码不正确")
        else:
            print("登录成功")
            return True  # 登录成功
        return False

    def checkbook(self):
        while True:
            bookname = input("请输入需要检索的书目（按#返回,按*返回所有书目）: ")
            if bookname == '#':
                break
            elif bookname == '*':
                print(self.warehouse.retriveAll())
            else:
                print(self.warehouse.retrive(bookname))

    def specialbook(self):
        print(self.bookstore.client_get_discounted_book())
        input("输入任意键继续")

    def buy(self):
        print(self.warehouse.retriveAll())

        # 开始下单
        while True:
            order = []
            bbuy = input("输入您要购买的书籍(按*完成): ")
            if bbuy == '*': break
            kind = input("输入您要购买的书籍的类别: ")
            number = input("请输入购买数量: ")
            # 数字判断
            ok = True
            for a in number:
                if a < '0' or a > '9':
                    ok = False
                break
            # 类型判断
            categories = ["杂志", "文化、社会", "摄影", "广告", "艺术", "文学"]
            if kind not in categories:
                ok = False

            if ok:
                # 判断书籍数量是否足够,但没有对重复购买进行判断，演示时需谨慎
                number = int(number)
                pur,situation = self.warehouse.buyonekind(bbuy, kind, number)
                if situation !=0:
                    print(pur)
                else:
                    print("下单成功")
                    order.append(pur["书籍类别"])
                    order.append(pur["书籍名称"])
                    order.append(float(pur["售价"]))
                    order.append(number)
                    toadd = number * float(pur["售价"])
                    order.append(toadd)
                    self.allmoney += toadd
                    self.purchase.append(order)
            else:
                print("输入不符合规范\n")

    def pay(self):
        print(self.purchase)
        if len(self.purchase) == 0:
            input("无书可买\n"
                  "按任意键退出\n")
            return

        self.bookstore.client_purchase(self.name, self.purchase)
        self.warehouse.buy(self.purchase)
        print("总价"+str(self.allmoney)+"元已支付成功")
        purchase = []
        self.allmoney = 0
        #暂停
        input("按任意键退出")

if __name__ == '__main__':
    warehouse = xmlrpc.client.ServerProxy("http://127.0.0.1:8002")
    bookstore = xmlrpc.client.ServerProxy("http://127.0.0.1:8001")
    client = Client(warehouse,bookstore)

    while True:
        # 登录模块
        while True:
            choice = input("\n\n      登录界面      \n"
                           "1.注册\n"
                           "2.登录\n")
            if choice == '1':
                client.register()
                break
            elif choice == '2':
                if client.signin():
                    break
            else:
                print("输入不符合规范，请重新输入\n\n\n")

        #服务模块
        while True:
            choice = input("\n\n尊敬的 "+ client.name + " ,请选择您需要的服务 \n"
                           "1.书目检索\n"
                           "2.特价书籍\n"
                           "3.下单\n"
                           "4.付款\n"
                           "5.退出\n")
            if choice == '1': client.checkbook()
            elif choice == '2':client.specialbook()
            elif choice == '3':client.buy()
            elif choice == '4':client.pay()
            elif choice == '5':break
            else :print("输入不符合规范，请重新输入\n\n\n")