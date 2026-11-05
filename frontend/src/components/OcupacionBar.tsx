interface Props {
  ocupado: number
}

export function OcupacionBar({ ocupado }: Props) {
  const libre = Math.max(0, 100 - ocupado)
  return (
    <div className="ocupacion">
      <div className="ocupacion-track" aria-hidden="true">
        <div
          className={`ocupacion-fill${ocupado >= 100 ? ' is-full' : ''}`}
          style={{ width: `${Math.min(100, ocupado)}%` }}
        />
      </div>
      <div className="ocupacion-nums">
        <span>
          Ocupado <strong>{ocupado}%</strong>
        </span>
        <span>
          Libre <strong>{libre}%</strong>
        </span>
      </div>
    </div>
  )
}
