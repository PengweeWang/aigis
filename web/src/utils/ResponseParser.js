/**
 * 后端JSON响应统一解析工具
 */
class ResponseParser {
  /**
   * 解析响应入口
   * @param {Object} response 后端返回的JSON响应
   * @returns {Object} 解析后的结果，包含type、data、mapActions等
   */
  parse(response) {
    if (!response || !response.schema_version) {
      return {
        type: 'text',
        data: { content: '响应格式错误' }
      }
    }

    const { response_type, business_type, data } = response

    // 处理交互选择类型
    if (response_type === 'interactive_selection') {
      return this.parseInteractiveSelection(data)
    }

    // 处理错误类型
    if (response_type === 'error') {
      return this.parseError(data)
    }

    // 处理成功响应
    if (response_type === 'success') {
      switch (business_type) {
        case 'geocode':
          return this.parseGeocode(data)
        case 'distance':
          return this.parseDistance(data)
        case 'route':
          return this.parseRoute(data)
        default:
          return {
            type: 'text',
            data: { content: JSON.stringify(data, null, 2) }
          }
      }
    }

    return {
      type: 'text',
      data: { content: '未知响应类型' }
    }
  }

  /**
   * 解析坐标查询结果
   */
  parseGeocode(data) {
    const { location, formatted_address, address_component } = data
    const [lng, lat] = this.parseLocation(location)

    return {
      type: 'geocode',
      data: {
        address: formatted_address,
        location: [lng, lat],
        province: address_component?.province,
        city: address_component?.city,
        district: address_component?.district
      },
      mapActions: [
        {
          action: 'addMarker',
          params: {
            position: [lng, lat],
            title: formatted_address,
            content: `
              <div>
                <h4>${formatted_address}</h4>
                <p>${address_component?.province || ''} ${address_component?.city || ''} ${address_component?.district || ''}</p>
                <p>坐标：${lng}, ${lat}</p>
              </div>
            `
          }
        },
        {
          action: 'setCenter',
          params: { position: [lng, lat], zoom: 15 }
        }
      ]
    }
  }

  /**
   * 解析距离计算结果
   */
  parseDistance(data) {
    const { origin, destination, distance_m, distance_km } = data
    const originLngLat = this.parseLocation(origin.location)
    const destLngLat = this.parseLocation(destination.location)

    return {
      type: 'distance',
      data: {
        origin: {
          address: origin.address,
          location: originLngLat
        },
        destination: {
          address: destination.address,
          location: destLngLat
        },
        distance_m,
        distance_km
      },
      mapActions: [
        {
          action: 'clearMarkers'
        },
        {
          action: 'clearPolylines'
        },
        {
          action: 'addMarker',
          params: {
            position: originLngLat,
            title: '起点：' + origin.address,
            icon: 'start',
            content: `<div><h4>起点</h4><p>${origin.address}</p></div>`
          }
        },
        {
          action: 'addMarker',
          params: {
            position: destLngLat,
            title: '终点：' + destination.address,
            icon: 'end',
            content: `<div><h4>终点</h4><p>${destination.address}</p></div>`
          }
        },
        {
          action: 'addPolyline',
          params: {
            path: [originLngLat, destLngLat],
            strokeColor: '#1890ff',
            strokeWeight: 4,
            strokeOpacity: 0.8
          }
        },
        {
          action: 'setFitView',
          params: { positions: [originLngLat, destLngLat] }
        }
      ]
    }
  }

  /**
   * 解析路径规划结果
   */
  parseRoute(data) {
    const { mode, origin, destination, distance_m, duration_s, route_polyline, steps, additional_info } = data
    const originLngLat = this.parseLocation(origin.location)
    const destLngLat = this.parseLocation(destination.location)

    // 转换路径点格式
    const path = route_polyline.map(point => this.parseLocation(point.join(',')))

    // 格式化时间
    const durationText = this.formatDuration(duration_s)

    return {
      type: 'route',
      data: {
        mode,
        origin: {
          address: origin.address,
          location: originLngLat
        },
        destination: {
          address: destination.address,
          location: destLngLat
        },
        distance_m,
        distance_km: (distance_m / 1000).toFixed(1),
        duration_s,
        durationText,
        steps,
        tolls: additional_info?.tolls,
        taxi_cost: additional_info?.taxi_cost
      },
      mapActions: [
        {
          action: 'clearMarkers'
        },
        {
          action: 'clearPolylines'
        },
        {
          action: 'addMarker',
          params: {
            position: originLngLat,
            title: '起点：' + origin.address,
            icon: 'start',
            content: `<div><h4>起点</h4><p>${origin.address}</p></div>`
          }
        },
        {
          action: 'addMarker',
          params: {
            position: destLngLat,
            title: '终点：' + destination.address,
            icon: 'end',
            content: `<div><h4>终点</h4><p>${destination.address}</p></div>`
          }
        },
        {
          action: 'addPolyline',
          params: {
            path,
            strokeColor: mode === 'driving' ? '#52c41a' : mode === 'cycling' ? '#fa8c16' : '#1890ff',
            strokeWeight: 5,
            strokeOpacity: 0.8
          }
        },
        {
          action: 'setFitView',
          params: { positions: [originLngLat, destLngLat] }
        }
      ]
    }
  }

  /**
   * 解析交互选择响应
   */
  parseInteractiveSelection(data) {
    const { selection_type, message, options } = data

    return {
      type: 'selection',
      data: {
        selection_type,
        message,
        options: options.map(option => ({
          id: option.id,
          label: option.address,
          value: option.location,
          address: option.address,
          location: this.parseLocation(option.location)
        }))
      },
      mapActions: [] // 选择类响应默认不操作地图，用户选择后再处理
    }
  }

  /**
   * 解析错误响应
   */
  parseError(data) {
    const { error_code, error_message } = data

    return {
      type: 'error',
      data: {
        code: error_code,
        message: error_message
      },
      mapActions: []
    }
  }

  /**
   * 解析坐标字符串 "lng,lat" 转为数组 [lng, lat]
   */
  parseLocation(locationStr) {
    if (!locationStr) return [0, 0]
    const parts = locationStr.split(',').map(Number)
    return [parts[0] || 0, parts[1] || 0]
  }

  /**
   * 格式化秒数为可读时间
   */
  formatDuration(seconds) {
    if (!seconds) return ''
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`
    } else {
      return `${minutes}分钟`
    }
  }
}

export default new ResponseParser()