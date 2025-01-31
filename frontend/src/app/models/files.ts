export interface VideoInfo {
  name: string
  format_name: string
  duration: string
  size: number
  bitrate: string
  streams: StreamInfo[]
}

export interface StreamInfo {
  index: number
  codec_type: string
  codec_name: string
  coded_height: number
  coded_width: number
  audio_channels: number
  sample_rate: number
  language: string
  duration: string
}