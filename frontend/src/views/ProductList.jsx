import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Input, Select, Pagination, Typography, Spin, Button } from 'antd'
import { SearchOutlined, ShoppingCartOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'

const { Title } = Typography
const { Meta } = Card
const { Option } = Select

const ProductList = () => {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(12)

  useEffect(() => {
    fetchProducts()
  }, [currentPage])

  const fetchProducts = async () => {
    setLoading(true)
    try {
      // 这里应该调用获取商品列表的API
      // 模拟数据
      const mockProducts = Array.from({ length: 12 }, (_, i) => ({
        id: i + 1,
        title: `商品 ${i + 1}`,
        price: (Math.random() * 1000).toFixed(2),
        image: 'https://via.placeholder.com/300x300',
        description: `这是商品 ${i + 1} 的描述信息`
      }))
      
      setProducts(mockProducts)
      setTotal(100)
    } catch (error) {
      console.error('获取商品列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePageChange = (page) => {
    setCurrentPage(page)
  }

  return (
    <div>
      <Title level={2}>商品列表</Title>
      
      <div style={{ marginBottom: 20, display: 'flex', justifyContent: 'space-between' }}>
        <Input
          placeholder="搜索商品..."
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
        />
        
        <Select defaultValue="all" style={{ width: 120 }}>
          <Option value="all">全部分类</Option>
          <Option value="electronics">电子产品</Option>
          <Option value="clothing">服装</Option>
          <Option value="books">图书</Option>
        </Select>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Row gutter={[24, 24]}>
            {products.map(product => (
              <Col key={product.id} span={6}>
                <Card
                  hoverable
                  cover={<img alt={product.title} src={product.image} />}
                  actions={[
                    <Button type="primary" icon={<ShoppingCartOutlined />} key="cart">
                      加入购物车
                    </Button>
                  ]}
                >
                  <Meta
                    title={<Link to={`/products/${product.id}`}>{product.title}</Link>}
                    description={
                      <div>
                        <div style={{ color: 'red', fontWeight: 'bold' }}>¥{product.price}</div>
                        <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                          {product.description}
                        </div>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>

          <div style={{ textAlign: 'center', marginTop: '30px' }}>
            <Pagination
              current={currentPage}
              pageSize={pageSize}
              total={total}
              onChange={handlePageChange}
              showSizeChanger={false}
            />
          </div>
        </>
      )}
    </div>
  )
}

export default ProductList