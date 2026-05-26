// Plain JavaScript (not TS) — use JSDoc for incremental TypeScript

/** @typedef {'user' | 'assistant' | 'system'} MessageRole */

/** @typedef {{ label: string, lng: number, lat: number, uid?: string }} UserPoint */

/**
 * @typedef {Object} ModelOption
 * @property {string} value
 * @property {string} providerID
 * @property {string} label
 */

/**
 * @typedef {Object} ToolState
 * @property {'running' | 'completed' | 'error'} status
 * @property {Object} input
 * @property {string} [input.description]
 * @property {string} [input.prompt]
 * @property {'geocoder' | 'distance-measure' | 'route-planner'} [input.subagent_type]
 * @property {boolean} [input.isFinal]
 * @property {string} [output]
 * @property {string} [title]
 * @property {Object} [time]
 * @property {number} [time.start]
 * @property {number} [time.end]
 */

/**
 * @typedef {Object} Part
 * @property {string} id
 * @property {string} sessionID
 * @property {string} messageID
 * @property {'text' | 'reasoning' | 'tool' | 'step-start' | 'step-finish'} type
 * @property {string} [text]
 * @property {string} [callID]
 * @property {string} [tool]
 * @property {ToolState} [state]
 * @property {string} [reason]
 */

/**
 * @typedef {Object} Message
 * @property {string} id
 * @property {'message' | 'reasoning' | 'system'} type
 * @property {MessageRole} [role]
 * @property {string} [content]
 * @property {boolean} [typing]
 * @property {boolean} [loading]
 * @property {UserPoint[]} [points]
 * @property {string} [userText]
 * @property {boolean} [expanded]
 * @property {Part[]} [toolCalls]
 */

/**
 * @typedef {Object} SsePayload
 * @property {string} type
 * @property {Object} properties
 * @property {string} [properties.sessionID]
 * @property {Object} [properties.info]
 * @property {string} [properties.info.id]
 * @property {string} [properties.info.role]
 * @property {Part} [properties.part]
 * @property {string} [properties.messageID]
 * @property {string} [properties.partID]
 * @property {string} [properties.delta]
 */

/**
 * @typedef {'points' | 'polyline' | 'distance'} WsDataType
 *
 * @typedef {Object} WsPointItem
 * @property {{ lng: number, lat: number }} location
 * @property {string} [formatted_address]
 * @property {string} [address]
 *
 * @typedef {Object} WsPolylineItem
 * @property {{ lng: number, lat: number, address?: string }} [origin]
 * @property {{ lng: number, lat: number, address?: string }} [destination]
 * @property {{ lng: number, lat: number }[]} [polyline]
 *
 * @typedef {Object} WsMessage
 * @property {WsDataType} type
 * @property {(WsPointItem[] | WsPolylineItem[])} data
 */

export {}
