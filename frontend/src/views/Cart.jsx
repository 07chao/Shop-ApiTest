import React, { useState } from 'react'
import { Table, Button, InputNumber, Typography, Card, Checkbox, Divider, message } from 'antd'
import { DeleteOutlined, ShoppingOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'

const { Title } = Typography

const Cart = () => {
  const [cartItems, setCartItems] = useState([
    {
      id: 1,
      productId: 1,
      title: '商品 1',
      image: 'https://via.placeholder.com/100x100',
      price: 299.99,
      quantity: 2,
      checked: true
    },
    {
      id: 2,
      productId: 2,
      title: '商品 2',
      image: 'https://via.placeholder.com/100x100',
      price: 199.99,
      quantity: 1,
      checked: true
    }
  ])

  const handleQuantityChange = (id, quantity) => {
    setCartItems(items =>
      items.map(item =>
        item.id === id ? { ...item, quantity } : item
      )
    )
  }

  const handleDelete = (id) => {
    setCartItems(items => items.filter(item => item.id !== id))
    message.success('已删除商品')
  }

  const handleCheck = (id, checked) => {
    setCartItems(items =>
      items.map(item =>
        item.id === id ? { ...item, checked } : item
      )
    )
  }

  const handleCheckAll = (e) => {
    const checked = e.target.checked
    setCartItems(items =>
      items.map(item => ({ ...item, checked }))
    )
  }

  const totalAmount = cartItems
    .filter(item => item.checked)
    .reduce((sum, item) => sum + item.price * item.quantity, 0)

  const checkedCount = cartItems.filter(item => item.checked).length

  const columns = [
    {
      title: '商品信息',
      dataIndex: 'product',
      render: (_, record) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Checkbox
            checked={record.checked}
            onChange={e => handleCheck(record.id, e.target.checked)}
          />
          <img
            src={record.image}
            alt={record.title}
            style={{ width: 80, height: 80, marginLeft: 10, marginRight: 20 }}
          />
          <Link to={`/products/${record.productId}`}>{record.title}</Link>
        </div>
      )
    },
    {
      title: '单价',
      dataIndex: 'price',
      render: price => `¥${price.toFixed(2)}`
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      render: (_, record) => (
        <InputNumber
          min={1}
          max={100}
          value={record.quantity}
          onChange={value => handleQuantityChange(record.id, value)}
        />
      )
    },
    {
      title: '小计',
      dataIndex: 'subtotal',
      render: (_, record) => `¥${(record.price * record.quantity).toFixed(2)}`
    },
    {
      title: '操作',
      dataIndex: 'action',
      render: (_, record) => (
        <Button
          type="text"
          icon={<DeleteOutlined />}
          onClick={() => handleDelete(record.id)}
          danger
        >
          删除
        </Button>
      )
    }
  ]

  return (
    <div>
      <Title level={2}>购物车</Title>
      
      <Table
        columns={columns}
        dataSource={cartItems}
        pagination={false}
        rowKey="id"
        footer={() => (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Checkbox
                onChange={handleCheckAll}
                checked={checkedCount === cartItems.length && cartItems.length > 0}
                indeterminate={checkedCount > 0 && checkedCount < cartItems.length}
              >
                全选
              </Checkbox>
              <Button type="link" onClick={() => setCartItems([])} danger>
                清空购物车
              </Button>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div>
                已选择 {checkedCount} 件商品
                <span style={{ margin: '0 20px' }}>合计: </span>
                <span style={{ fontSize: 20, color: 'red', fontWeight: 'bold' }}>
                  ¥{totalAmount.toFixed(2)}
                </span>
              </div>
              <Link to="/checkout">
                <Button
                  type="primary"
                  size="large"
                  icon={<ShoppingOutlined />}
                  disabled={checkedCount === 0}
                  style={{ marginTop: 10 }}
                >
                  去结算
                </Button>
              </Link>
            </div>
          </div>
        )}
      />
    </div>
  )
}

export default Cart