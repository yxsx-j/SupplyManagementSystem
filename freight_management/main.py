#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
货源管理系统 - 命令行版本 (CLI)
数据持久化：JSON文件存储
"""

import json
import os
import datetime
from typing import List, Dict, Optional
import pandas as pd

# 数据文件路径
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')


class FreightManagementCLI:
    """货源管理系统命令行类"""
    
    def __init__(self):
        self.freights: List[Dict] = []
        self.load_data()
    
    def load_data(self) -> None:
        """从JSON文件加载数据"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.freights = json.load(f)
                print(f"✓ 成功加载 {len(self.freights)} 条货源记录")
            except Exception as e:
                print(f"✗ 加载数据失败: {e}")
                self.freights = []
        else:
            print("ℹ 数据文件不存在，将创建新的数据文件")
            self.freights = []
    
    def save_data(self) -> None:
        """保存数据到JSON文件"""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.freights, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"✗ 保存数据失败: {e}")
    
    def generate_id(self) -> int:
        """生成唯一ID"""
        if not self.freights:
            return 1
        return max(f['id'] for f in self.freights) + 1
    
    def calculate_total(self, tonnage: float, price: float) -> float:
        """计算总价"""
        return round(tonnage * price, 2)
    
    def publish_freight(self) -> None:
        """发布货源"""
        print("\n" + "="*50)
        print("【发布货源】")
        print("="*50)
        
        try:
            date = input("请输入日期 (YYYY-MM-DD，默认今天): ").strip()
            if not date:
                date = datetime.date.today().strftime('%Y-%m-%d')
            
            origin = input("请输入发货地: ").strip()
            while not origin:
                origin = input("发货地不能为空，请重新输入: ").strip()
            
            destination = input("请输入卸货地: ").strip()
            while not destination:
                destination = input("卸货地不能为空，请重新输入: ").strip()
            
            tonnage = float(input("请输入吨位: ").strip())
            while tonnage <= 0:
                tonnage = float(input("吨位必须大于0，请重新输入: ").strip())
            
            vehicle_type = input("请输入需用车型: ").strip()
            while not vehicle_type:
                vehicle_type = input("车型不能为空，请重新输入: ").strip()
            
            price = float(input("请输入单价 (元/吨): ").strip())
            while price <= 0:
                price = float(input("单价必须大于0，请重新输入: ").strip())
            
            tax_included = input("是否含税? (y/n，默认n): ").strip().lower()
            tax_included = tax_included == 'y'
            
            payment_method = input("请输入结算方式 (如: 现结/周结/月结): ").strip()
            while not payment_method:
                payment_method = input("结算方式不能为空，请重新输入: ").strip()
            
            order_person = input("请输入下单人: ").strip()
            while not order_person:
                order_person = input("下单人不能为空，请重新输入: ").strip()
            
            total = self.calculate_total(tonnage, price)
            print(f"\n自动计算总价: {total} 元")
            
            freight = {
                'id': self.generate_id(),
                'date': date,
                'origin': origin,
                'destination': destination,
                'tonnage': tonnage,
                'vehicle_type': vehicle_type,
                'price': price,
                'tax_included': tax_included,
                'payment_method': payment_method,
                'order_person': order_person,
                'total': total,
                'status': 'pending',
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.freights.append(freight)
            self.save_data()
            print(f"\n✓ 货源发布成功！货源ID: {freight['id']}")
            
        except ValueError as e:
            print(f"✗ 输入错误: {e}")
        except Exception as e:
            print(f"✗ 发布失败: {e}")
    
    def view_pending_freights(self) -> None:
        """查看待报价货源列表"""
        pending = [f for f in self.freights if f['status'] == 'pending']
        
        if not pending:
            print("\nℹ 暂无待报价货源")
            return
        
        print("\n" + "="*80)
        print(f"【待报价货源列表】共 {len(pending)} 条")
        print("="*80)
        print(f"{'ID':<4} {'日期':<12} {'发货地':<10} {'卸货地':<10} {'吨位':<6} {'车型':<10} {'单价':<8} {'总价':<10} {'下单人':<8}")
        print("-"*80)
        
        for f in pending:
            print(f"{f['id']:<4} {f['date']:<12} {f['origin']:<10} {f['destination']:<10} "
                  f"{f['tonnage']:<6} {f['vehicle_type']:<10} {f['price']:<8} {f['total']:<10} {f['order_person']:<8}")
    
    def handle_quote(self) -> None:
        """处理货源报价"""
        self.view_pending_freights()
        
        pending = [f for f in self.freights if f['status'] == 'pending']
        if not pending:
            return
        
        try:
            freight_id = int(input("\n请输入要处理的货源ID: ").strip())
            freight = next((f for f in self.freights if f['id'] == freight_id and f['status'] == 'pending'), None)
            
            if not freight:
                print("✗ 未找到该货源或货源已处理")
                return
            
            print("\n" + "="*50)
            print("货源详情:")
            for key, value in freight.items():
                print(f"  {key}: {value}")
            print("="*50)
            
            choice = input("\n请选择操作 (1-同意报价 2-拒绝并修改 0-取消): ").strip()
            
            if choice == '1':
                freight['status'] = 'success'
                freight['completed_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.save_data()
                print("✓ 报价已同意，货源已移入交易成功列表")
                
            elif choice == '2':
                print("\n【修改货源信息】(直接回车保留原值)")
                freight['origin'] = input(f"发货地 ({freight['origin']}): ").strip() or freight['origin']
                freight['destination'] = input(f"卸货地 ({freight['destination']}): ").strip() or freight['destination']
                
                new_tonnage = input(f"吨位 ({freight['tonnage']}): ").strip()
                if new_tonnage:
                    freight['tonnage'] = float(new_tonnage)
                
                freight['vehicle_type'] = input(f"车型 ({freight['vehicle_type']}): ").strip() or freight['vehicle_type']
                
                new_price = input(f"单价 ({freight['price']}): ").strip()
                if new_price:
                    freight['price'] = float(new_price)
                
                freight['total'] = self.calculate_total(freight['tonnage'], freight['price'])
                self.save_data()
                print(f"✓ 货源已修改，新总价: {freight['total']} 元")
                
            else:
                print("已取消操作")
                
        except ValueError as e:
            print(f"✗ 输入错误: {e}")
        except Exception as e:
            print(f"✗ 处理失败: {e}")
    
    def view_success_freights(self) -> None:
        """查看交易成功货源列表"""
        success = [f for f in self.freights if f['status'] == 'success']
        
        if not success:
            print("\nℹ 暂无交易成功货源")
            return
        
        print("\n" + "="*90)
        print(f"【交易成功货源列表】共 {len(success)} 条")
        print("="*90)
        print(f"{'ID':<4} {'日期':<12} {'发货地':<10} {'卸货地':<10} {'吨位':<6} {'车型':<10} {'总价':<10} {'下单人':<8} {'完成时间':<20}")
        print("-"*90)
        
        for f in success:
            print(f"{f['id']:<4} {f['date']:<12} {f['origin']:<10} {f['destination']:<10} "
                  f"{f['tonnage']:<6} {f['vehicle_type']:<10} {f['total']:<10} {f['order_person']:<8} {f.get('completed_at', ''):<20}")
    
    def export_data(self) -> None:
        """导出数据为CSV或Excel"""
        success = [f for f in self.freights if f['status'] == 'success']
        
        if not success:
            print("\nℹ 暂无数据可导出")
            return
        
        print("\n【数据导出】")
        print("1. 导出为 CSV 格式")
        print("2. 导出为 Excel 格式")
        
        choice = input("请选择导出格式: ").strip()
        
        try:
            df = pd.DataFrame(success)
            
            if choice == '1':
                filename = f"交易成功货源_{datetime.date.today()}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"✓ 数据已导出到: {filename}")
                
            elif choice == '2':
                filename = f"交易成功货源_{datetime.date.today()}.xlsx"
                df.to_excel(filename, index=False)
                print(f"✓ 数据已导出到: {filename}")
                
            else:
                print("✗ 无效的选择")
                
        except Exception as e:
            print(f"✗ 导出失败: {e}")
    
    def show_menu(self) -> None:
        """显示主菜单"""
        print("\n" + "="*50)
        print("      货源管理系统 - 命令行版本")
        print("="*50)
        print("1. 发布货源")
        print("2. 货源报价处理")
        print("3. 查看待报价货源")
        print("4. 查看交易成功货源")
        print("5. 导出交易成功数据")
        print("0. 退出系统")
        print("="*50)
    
    def run(self) -> None:
        """运行主程序"""
        print("\n欢迎使用货源管理系统 CLI 版本！")
        
        while True:
            self.show_menu()
            choice = input("请选择操作: ").strip()
            
            if choice == '0':
                print("\n感谢使用，再见！")
                break
            elif choice == '1':
                self.publish_freight()
            elif choice == '2':
                self.handle_quote()
            elif choice == '3':
                self.view_pending_freights()
            elif choice == '4':
                self.view_success_freights()
            elif choice == '5':
                self.export_data()
            else:
                print("✗ 无效的选择，请重新输入")
            
            input("\n按回车键继续...")


if __name__ == '__main__':
    app = FreightManagementCLI()
    app.run()
