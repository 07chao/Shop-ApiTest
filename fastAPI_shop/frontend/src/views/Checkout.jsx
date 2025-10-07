import React, { useState } from 'react'
import { Steps, Card, Typography, List, Divider, Button, message, Row, Col } from 'antd'
import { UserOutlined, EnvironmentOutlined, CreditCardOutlined, CheckOutlined } from '@ant-design/icons'

const { Title } = Typography

const Checkout = () => {
  const [currentStep, setCurrentStep] = useState(0)

  // 模拟购物车商品
  const cartItems = [
    {
      id: 1,
      title: '商品 1',
      price: 299.99,
      quantity: 2,
      image: 'https://via.placeholder.com/100x100'
    },
    {
      id: 2,
      title: '商品 2',
      price: 199.99,
      quantity: 1,
      image: 'https://via.placeholder.com/100x100'
    }
  ]

  const totalAmount = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0)
  const shippingFee = 0
  const discount = 0
  const finalAmount = totalAmount + shippingFee - discount

  const steps = [
    {
      title: '确认订单',
      icon: <UserOutlined />
    },
    {
      title: '选择支付',
      icon: <CreditCardOutlined />
    },
    {
      title: '完成支付',
      icon: <CheckOutlined />
    }
  ]

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      message.success('支付成功！')
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Row gutter={24}>
            <Col span={16}>
              <Card title="收货地址">
                <div style={{ padding: '20px', border: '1px solid #f0f0f0', borderRadius: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div>
                      <div><strong>张三</strong> 138****1234</div>
                      <div>北京市朝阳区某某街道某某小区1号楼101室</div>
                    </div>
                    <Button type="link">修改</Button>
                  </div>
                </div>
              </Card>

              <Card title="商品清单" style={{ marginTop: 20 }}>
                <List
                  itemLayout="horizontal"
                  dataSource={cartItems}
                  renderItem={item => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<img src={item.image} alt={item.title} style={{ width: 60, height: 60 }} />}
                        title={item.title}
                        description={`数量: ${item.quantity}`}
                      />
                      <div>¥{(item.price * item.quantity).toFixed(2)}</div>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>

            <Col span={8}>
              <Card title="订单汇总">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span>商品总价:</span>
                  <span>¥{totalAmount.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span>运费:</span>
                  <span>¥{shippingFee.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span>优惠:</span>
                  <span>-¥{discount.toFixed(2)}</span>
                </div>
                <Divider style={{ margin: '10px 0' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                  <span>应付总额:</span>
                  <span style={{ color: 'red', fontSize: 18 }}>¥{finalAmount.toFixed(2)}</span>
                </div>
              </Card>
            </Col>
          </Row>
        )
      case 1:
        return (
          <Card title="选择支付方式">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div
                style={{
                  padding: '20px',
                  border: '1px solid #1890ff',
                  borderRadius: '4px',
                  backgroundColor: '#e6f7ff'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <CreditCardOutlined style={{ fontSize: 24, marginRight: 10 }} />
                  <div>
                    <div style={{ fontWeight: 'bold' }}>在线支付</div>
                    <div>支持微信、支付宝、银行卡等多种方式</div>
                  </div>
                </div>
              </div>

              <div
                style={{
                  padding: '20px',
                  border: '1px solid #f0f0f0',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
                onClick={() => message.info('暂不支持货到付款')}
              >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <EnvironmentOutlined style={{ fontSize: 24, marginRight: 10 }} />
                  <div>
                    <div style={{ fontWeight: 'bold' }}>货到付款</div>
                    <div>收到商品时现金支付</div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )
      case 2:
        return (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <div style={{ fontSize: 48, color: '#52c41a', marginBottom: 20 }}>
              <CheckOutlined />
            </div>
            <Title level={2} style={{ marginBottom: 20 }}>支付成功</Title>
            <p>订单号: ORD202310250001</p>
            <p>支付金额: ¥{finalAmount.toFixed(2)}</p>
            <div style={{ marginTop: 30 }}>
              <Button type="primary" style={{ marginRight: 20 }}>
                查看订单
              </Button>
              <Button>继续购物</Button>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div>
      <Title level={2}>结算</Title>
      
      <Steps
        current={currentStep}
        items={steps.map(step => ({
          key: step.title,
          title: step.title,
          icon: step.icon
        }))}
        style={{ marginBottom: 30 }}
      />

      {renderStepContent()}

      {currentStep < 2 && (
        <div style={{ textAlign: 'center', marginTop: 30 }}>
          {currentStep > 0 && (
            <Button onClick={handlePrev} style={{ marginRight: 20 }}>
              上一步
            </Button>
          )}
          <Button type="primary" onClick={handleNext}>
            {currentStep === steps.length - 2 ? '支付' : '下一步'}
          </Button>
        </div>
      )}
    </div>
  )
}

export default Checkout