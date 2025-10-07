import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Row, Col, Typography, Image, Button, InputNumber, Card, Rate, Divider, message } from 'antd'
import { ShoppingCartOutlined, StarOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const ProductDetail = () => {
  const { id } = useParams()
  const [quantity, setQuantity] = useState(1)

  // 模拟商品数据
  const product = {
    id: id,
    title: `商品 ${id}`,
    price: (Math.random() * 1000).toFixed(2),
    originalPrice: (Math.random() * 1200).toFixed(2),
    image: 'https://via.placeholder.com/500x500',
    images: [
      'https://via.placeholder.com/100x100',
      'https://via.placeholder.com/100x100',
      'https://via.placeholder.com/100x100'
    ],
    description: `这是商品 ${id} 的详细描述信息。商品质量上乘，性价比高，深受消费者喜爱。`,
    rating: 4.5,
    reviewCount: 128,
    stock: 100
  }

  const handleAddToCart = () => {
    // 这里应该调用加入购物车的API
    message.success('已加入购物车')
  }

  const handleBuyNow = () => {
    // 这里应该跳转到结算页面
    message.info('立即购买')
  }

  return (
    <div>
      <Title level={2}>{product.title}</Title>
      
      <Row gutter={24}>
        <Col span={12}>
          <Image
            width="100%"
            src={product.image}
          />
          <div style={{ marginTop: 20 }}>
            <Row gutter={10}>
              {product.images.map((img, index) => (
                <Col key={index} span={6}>
                  <Image
                    src={img}
                    preview={false}
                    style={{ border: '1px solid #f0f0f0', cursor: 'pointer' }}
                  />
                </Col>
              ))}
            </Row>
          </div>
        </Col>
        
        <Col span={12}>
          <Card>
            <Title level={3} style={{ color: 'red' }}>¥{product.price}</Title>
            <Text delete>¥{product.originalPrice}</Text>
            <div style={{ marginTop: 10 }}>
              <Rate disabled defaultValue={product.rating} />
              <Text style={{ marginLeft: 10 }}>{product.rating} ({product.reviewCount} 条评价)</Text>
            </div>
            
            <Divider />
            
            <div style={{ marginBottom: 20 }}>
              <Text strong>库存：</Text>
              <Text>{product.stock} 件</Text>
            </div>
            
            <div style={{ marginBottom: 20 }}>
              <Text strong>数量：</Text>
              <InputNumber
                min={1}
                max={product.stock}
                defaultValue={1}
                value={quantity}
                onChange={setQuantity}
              />
            </div>
            
            <div>
              <Button
                type="primary"
                icon={<ShoppingCartOutlined />}
                size="large"
                onClick={handleAddToCart}
                style={{ marginRight: 20 }}
              >
                加入购物车
              </Button>
              <Button
                type="danger"
                size="large"
                onClick={handleBuyNow}
              >
                立即购买
              </Button>
            </div>
          </Card>
        </Col>
      </Row>
      
      <Divider />
      
      <Card title="商品详情">
        <Text>{product.description}</Text>
      </Card>
    </div>
  )
}

export default ProductDetail