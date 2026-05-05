#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
货源管理系统 - Web版本 (Flask)
数据持久化：SQLite数据库
仅保留Excel导出功能，且导出字段为中文
"""

import os
import datetime
from flask import Flask, render_template, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from io import BytesIO
from urllib.parse import quote  # 解决中文文件名编码问题，确保Excel导出正常

# 初始化Flask应用
app = Flask(__name__)

# 配置SQLite数据库
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'freight.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义字段中英文映射（核心：导出Excel时显示中文字段名）
FIELD_NAME_MAPPING = {
    'id': '货源ID',
    'date': '日期',
    'origin': '发货地',
    'destination': '卸货地',
    'tonnage': '吨位（吨）',
    'vehicle_type': '需用车型',
    'price': '单价（元/吨）',
    'tax_included': '是否含税',
    'payment_method': '结算方式',
    'order_person': '下单人',
    'total': '总价（元）',
    'status': '状态',
    'created_at': '创建时间',
    'completed_at': '完成时间'
}


class Freight(db.Model):
    """货源数据模型"""
    __tablename__ = 'freights'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.String(20), nullable=False, comment='日期')
    origin = db.Column(db.String(100), nullable=False, comment='发货地')
    destination = db.Column(db.String(100), nullable=False, comment='卸货地')
    tonnage = db.Column(db.Float, nullable=False, comment='吨位')
    vehicle_type = db.Column(db.String(50), nullable=False, comment='需用车型')
    price = db.Column(db.Float, nullable=False, comment='单价')
    tax_included = db.Column(db.Boolean, default=False, comment='是否含税')
    payment_method = db.Column(db.String(50), nullable=False, comment='结算方式')
    order_person = db.Column(db.String(50), nullable=False, comment='下单人')
    total = db.Column(db.Float, nullable=False, comment='总价')
    status = db.Column(db.String(20), default='pending', comment='状态: pending/success')
    created_at = db.Column(db.String(30), nullable=False, comment='创建时间')
    completed_at = db.Column(db.String(30), comment='完成时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'date': self.date,
            'origin': self.origin,
            'destination': self.destination,
            'tonnage': self.tonnage,
            'vehicle_type': self.vehicle_type,
            'price': self.price,
            'tax_included': self.tax_included,
            'payment_method': self.payment_method,
            'order_person': self.order_person,
            'total': self.total,
            'status': self.status,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }


def calculate_total(tonnage: float, price: float) -> float:
    """计算总价"""
    return round(tonnage * price, 2)


@app.route('/')
def index():
    """首页 - 单页应用"""
    return render_template('index.html')


@app.route('/api/freights', methods=['GET'])
def get_freights():
    """获取所有货源列表"""
    status = request.args.get('status')
    search = request.args.get('search', '')

    query = Freight.query

    if status:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(
            (Freight.origin.contains(search)) |
            (Freight.destination.contains(search)) |
            (Freight.order_person.contains(search))
        )

    freights = query.order_by(Freight.id.desc()).all()
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': [f.to_dict() for f in freights]
    })


@app.route('/api/freights/<int:freight_id>', methods=['GET'])
def get_freight(freight_id):
    """获取单个货源详情"""
    freight = Freight.query.get(freight_id)
    if not freight:
        return jsonify({'code': 404, 'message': '货源不存在'}), 404

    return jsonify({
        'code': 0,
        'message': 'success',
        'data': freight.to_dict()
    })


@app.route('/api/freights', methods=['POST'])
def create_freight():
    """创建新货源"""
    try:
        data = request.get_json()

        required_fields = ['origin', 'destination', 'tonnage', 'vehicle_type',
                           'price', 'payment_method', 'order_person']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'code': 400, 'message': f'缺少必填字段: {field}'}), 400

        tonnage = float(data['tonnage'])
        price = float(data['price'])
        total = calculate_total(tonnage, price)

        freight = Freight(
            date=data.get('date', datetime.date.today().strftime('%Y-%m-%d')),
            origin=data['origin'],
            destination=data['destination'],
            tonnage=tonnage,
            vehicle_type=data['vehicle_type'],
            price=price,
            tax_included=data.get('tax_included', False),
            payment_method=data['payment_method'],
            order_person=data['order_person'],
            total=total,
            status='pending',
            created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        db.session.add(freight)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '货源发布成功',
            'data': freight.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'创建失败: {str(e)}'}), 500


@app.route('/api/freights/<int:freight_id>', methods=['PUT'])
def update_freight(freight_id):
    """更新货源信息"""
    try:
        freight = Freight.query.get(freight_id)
        if not freight:
            return jsonify({'code': 404, 'message': '货源不存在'}), 404

        data = request.get_json()

        if 'origin' in data:
            freight.origin = data['origin']
        if 'destination' in data:
            freight.destination = data['destination']
        if 'tonnage' in data:
            freight.tonnage = float(data['tonnage'])
        if 'vehicle_type' in data:
            freight.vehicle_type = data['vehicle_type']
        if 'price' in data:
            freight.price = float(data['price'])
        if 'tax_included' in data:
            freight.tax_included = data['tax_included']
        if 'payment_method' in data:
            freight.payment_method = data['payment_method']
        if 'order_person' in data:
            freight.order_person = data['order_person']
        if 'status' in data:
            freight.status = data['status']
            if data['status'] == 'success':
                freight.completed_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 重新计算总价
        freight.total = calculate_total(freight.tonnage, freight.price)

        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '更新成功',
            'data': freight.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'更新失败: {str(e)}'}), 500


@app.route('/api/freights/<int:freight_id>', methods=['DELETE'])
def delete_freight(freight_id):
    """删除货源"""
    try:
        freight = Freight.query.get(freight_id)
        if not freight:
            return jsonify({'code': 404, 'message': '货源不存在'}), 404

        db.session.delete(freight)
        db.session.commit()

        return jsonify({'code': 0, 'message': '删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'删除失败: {str(e)}'}), 500


@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    """导出Excel数据（仅保留此功能，删除CSV相关，导出字段为中文）"""
    try:
        status = request.args.get('status', 'success')
        freights = Freight.query.filter_by(status=status).all()

        if not freights:
            return jsonify({'code': 400, 'message': '暂无数据可导出'}), 400

        # 转换数据，优化Excel显示
        data = []
        for f in freights:
            freight_dict = f.to_dict()
            # 将布尔值转换为中文，提升Excel可读性
            freight_dict['tax_included'] = '是' if freight_dict['tax_included'] else '否'
            # 将状态英文转换为中文
            freight_dict['status'] = '待报价' if freight_dict['status'] == 'pending' else '交易成功'
            data.append(freight_dict)

        df = pd.DataFrame(data)
        # 调整列顺序，贴合实际使用习惯（与中文字段映射顺序一致）
        column_order = ['id', 'date', 'origin', 'destination', 'tonnage', 'vehicle_type',
                        'price', 'tax_included', 'payment_method', 'order_person',
                        'total', 'status', 'created_at', 'completed_at']
        df = df.reindex(columns=column_order)

        # 核心：将英文字段名替换为中文（使用映射字典）
        df = df.rename(columns=FIELD_NAME_MAPPING)

        # 生成文件名，对中文进行编码，避免乱码
        filename = f"交易成功货源_{datetime.date.today()}"
        encoded_filename = quote(filename, encoding='utf-8')

        # 写入Excel文件流，使用openpyxl引擎确保兼容性
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='货源数据')
        output.seek(0)  # 重置文件指针，确保正常读取

        # 构建响应，设置正确的响应头
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={encoded_filename}.xlsx'
        return response

    except Exception as e:
        # 打印错误信息，方便排查（部署时可按需删除）
        print(f"Excel导出失败详情: {str(e)}")
        return jsonify({'code': 500, 'message': f'Excel导出失败: {str(e)}'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    pending_count = Freight.query.filter_by(status='pending').count()
    success_count = Freight.query.filter_by(status='success').count()
    total_amount = db.session.query(db.func.sum(Freight.total)).filter_by(status='success').scalar() or 0

    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'pending_count': pending_count,
            'success_count': success_count,
            'total_amount': round(total_amount, 2)
        }
    })


def init_database():
    """初始化数据库，创建表并添加示例数据"""
    with app.app_context():
        db.create_all()

        # 检查是否已有数据
        if Freight.query.count() == 0:
            # 添加示例数据
            sample_data = [
                {
                    'date': '2026-04-28',
                    'origin': '石家庄',
                    'destination': '北京',
                    'tonnage': 30.0,
                    'vehicle_type': '13米高栏',
                    'price': 120.0,
                    'tax_included': True,
                    'payment_method': '现结',
                    'order_person': '张经理',
                    'total': 3600.0,
                    'status': 'pending',
                    'created_at': '2026-04-28 10:00:00'
                },
                {
                    'date': '2026-04-29',
                    'origin': '保定',
                    'destination': '天津',
                    'tonnage': 25.0,
                    'vehicle_type': '9.6米平板',
                    'price': 80.0,
                    'tax_included': False,
                    'payment_method': '周结',
                    'order_person': '李总',
                    'total': 2000.0,
                    'status': 'success',
                    'created_at': '2026-04-29 14:30:00',
                    'completed_at': '2026-04-29 16:00:00'
                }
            ]

            for data in sample_data:
                freight = Freight(**data)
                db.session.add(freight)

            db.session.commit()
            print("✓ 数据库初始化完成，已添加示例数据")
        else:
            print("✓ 数据库已存在，跳过初始化")


if __name__ == '__main__':
    init_database()
    print("\n" + "=" * 60)
    print("  货源管理系统 Web 版本启动成功！")
    print("=" * 60)
    print("  本地访问地址: http://localhost:5000")
    print("  数据库: SQLite (freight.db)")
    print("  导出功能: 仅支持Excel格式（中文字段）")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
