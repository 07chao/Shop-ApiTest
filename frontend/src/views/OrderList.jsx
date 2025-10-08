import React, { useState, useEffect } from 'react'
import { Table, Tag, Space, Button, Card, Typography } from 'antd'
import { EyeOutlined } from '@ant-design/icons'

const { Title } = Typography

const OrderList = () => {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchOrders()
  }, [])

  const fetchOrders = async () => {
    setLoading(true)
    try {
      // 模拟订单数据
      const mockOrders = [
        {
          id: 1,
          orderNumber: 'ORD202310250001',
          createdAt: '2023-10-25 10:30:00',
          totalAmount: 799.97,
          status: 'paid',
          items: [
            { id: 1, title: '商品 1', quantity: 2, price: 299.99 },
            { id: 2, title: '商品 2', quantity: 1, price: 199.99 }
          ]
        },
        {
          id: 2,
          orderNumber: 'ORD202310240002',
          createdAt: '2023-10-24 15:45:00',
          totalAmount: 299.99,
          status: 'shipped',
          items: [
            { id: 1, title: '商品 1', quantity: 1, price: 299.99 }
          ]
        },
        {
          id: 3,
          orderNumber: 'ORD202310230003',
          createdAt: '2023-10-23 09:15:00',
          totalAmount: 199.99,
          status: 'completed',
          items: [
            { id: 2, title: '商品 2', quantity: 1, price: 199.99 }
          ]
        }
      ]
      
      setOrders(mockOrders)
    } catch (error) {
      console.error('获取订单列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusTag = (status) => {
    switch (status) {
      case 'pending':
        return <Tag color="orange">待支付</Tag>
      case 'paid':
        return <Tag color="blue">已支付</Tag>
      case 'shipped':
        return <Tag color="purple">已发货</Tag>
      case 'completed':
        return <Tag color="green">已完成</Tag>
      case 'cancelled':
        return <Tag color="red">已取消</Tag>
      default:
        return <Tag>{status}</Tag>
    }
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'orderNumber',
      key: 'orderNumber'
    },
    {
      title: '下单时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: '订单金额',
      dataIndex: 'totalAmount',
      key: 'totalAmount',
      render: amount => `¥${amount.toFixed(2)}`
    },
    {
      title: '订单状态',
      dataIndex: 'status',
      key: 'status',
      render: status => getStatusTag(status)
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button type="link" icon={<EyeOutlined />}>
            查看详情
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <Title level={2}>我的订单</Title>
      
      <Card>
        <Table
          columns={columns}
          dataSource={orders}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10
          }}
        />
      </Card>
    </div>
  )
}

export default OrderList