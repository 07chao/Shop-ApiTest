import React from 'react'
import { Card, Col, Row, Typography, Button } from 'antd'
import { Link } from 'react-router-dom'

const { Title, Paragraph } = Typography

const Home = () => {
  return (
    <div>
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Title>欢迎来到FastAPI电商平台</Title>
        <Paragraph>一站式购物体验，品质保证，快速配送</Paragraph>
        <Link to="/products">
          <Button type="primary" size="large">
            开始购物
          </Button>
        </Link>
      </div>

      <Row gutter={24}>
        <Col span={8}>
          <Card title="品质保证" bordered={false}>
            <p>所有商品均经过严格筛选，确保品质</p>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="快速配送" bordered={false}>
            <p>全国范围内快速配送，准时送达</p>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="售后服务" bordered={false}>
            <p>7天无理由退货，贴心售后服务</p>
          </Card>
        </Col>
      </Row>

      <div style={{ textAlign: 'center', padding: '50px 0', marginTop: '50px' }}>
        <Title level={2}>热门商品</Title>
        <Paragraph>精选推荐，品质之选</Paragraph>
        {/* 这里应该展示热门商品列表 */}
      </div>
    </div>
  )
}

export default Home