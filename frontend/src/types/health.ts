export type ConnectionState = 'loading' | 'success' | 'error'
export interface CheckResult { state: ConnectionState; message: string }
export interface HealthResponse { status: 'ok' }
export interface DatabaseHealthResponse extends HealthResponse { database: 'connected' }
