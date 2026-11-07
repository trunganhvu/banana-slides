import React from 'react';

export type ReportFields = {
  topic: string; purpose: string; audience: string; style: string;
  pages: string; points: string; requirements: string;
};
export const emptyReport: ReportFields = {
  topic: '', purpose: '', audience: '', style: '', pages: '', points: '', requirements: '',
};
const labels = {
  zh: { topic: 'Chủ đề (bắt buộc) ', purpose: 'mục đích', audience: 'Đối tượng mục tiêu', style: 'Phong cách hình ảnh', pages: 'Số trang dự kiến', points: 'Ý chính nội dung', requirements: 'Yêu cầu bổ sung' },
  en: { topic: 'Topic (required)', purpose: 'Purpose', audience: 'Audience', style: 'Visual style', pages: 'Expected slides', points: 'Key points', requirements: 'Additional requirements' },
};
const presets = {
  zh: [
    ['Báo cáo tuần/Báo cáo tháng', 'Báo cáo tiến độ công việc kỳ này', 'Thành viên nhóm', 'Ngắn gọn, rõ ràng', '8'],
    ['Báo cáo dự án', 'Báo cáo kết quả giai đoạn dự án', 'Các bên liên quan dự án', 'Chuyên nghiệp, ngắn gọn', '10'],
    ['Giới thiệu sản phẩm', 'Giới thiệu sản phẩm và giá trị cốt lõi', 'Người dùng tiềm năng', 'Rõ ràng, trực quan', '10'],
    ['Bài giảng đào tạo', 'Trình bày kiến thức và phương pháp thực hành', 'Học viên đào tạo', 'Dễ đọc, dễ hiểu', '15'],
    ['Tùy chỉnh', '', '', '', ''],
  ],
  en: [
    ['Weekly / monthly report', 'Report progress this period', 'Team members', 'Clear and concise', '8'],
    ['Project update', 'Present project milestones', 'Project stakeholders', 'Professional and concise', '10'],
    ['Product introduction', 'Introduce the product and its value', 'Potential users', 'Clear and visual', '10'],
    ['Training', 'Explain concepts and practical methods', 'Learners', 'Easy to follow', '15'],
    ['Custom', '', '', '', ''],
  ],
};
export function buildReportPrompt(fields: ReportFields, zh: boolean): string {
  const names = labels[zh ? 'zh' : 'en'];
  return (Object.keys(fields) as (keyof ReportFields)[])
    .filter(key => fields[key].trim())
    .map(key => `${names[key]}: ${fields[key].trim()}`).join('\n');
}
export function applyReportPreset(fields: ReportFields, index: number, zh: boolean): ReportFields {
  const [, purpose, audience, style, pages] = presets[zh ? 'zh' : 'en'][index];
  return { ...fields, purpose: fields.purpose || purpose, audience: fields.audience || audience,
    style: fields.style || style, pages: fields.pages || pages };
}
export const ReportForm: React.FC<{
  fields: ReportFields; onChange: (fields: ReportFields) => void;
  onRebuild: () => void; zh: boolean; disabled: boolean;
}> = ({ fields, onChange, onRebuild, zh, disabled }) => {
  const names = labels[zh ? 'zh' : 'en'];
  return <fieldset disabled={disabled} className="space-y-3 mb-4" data-testid="report-form">
    <label className="block text-sm">
      {zh ? 'Mẫu kịch bản' : 'Scenario'}
      <select defaultValue="" className="block w-full p-2 border rounded-lg dark:bg-background-secondary" onChange={e => onChange(applyReportPreset(fields, Number(e.target.value), zh))}>
        <option value="" disabled>{zh ? 'Chọn kịch bản' : 'Choose a scenario'}</option>
        {presets[zh ? 'zh' : 'en'].map(([name], index) => <option key={index} value={index}>{name}</option>)}
      </select>
    </label>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {(Object.keys(names) as (keyof ReportFields)[]).map(key => <label key={key} className="text-sm">
        {names[key]}
        {key === 'points' || key === 'requirements'
          ? <textarea className="block w-full p-2 border rounded-lg dark:bg-background-secondary" value={fields[key]} onChange={e => onChange({ ...fields, [key]: e.target.value })} />
          : <input className="block w-full p-2 border rounded-lg dark:bg-background-secondary" type={key === 'pages' ? 'number' : 'text'} min={key === 'pages' ? 1 : undefined} required={key === 'topic'} value={fields[key]} onChange={e => onChange({ ...fields, [key]: e.target.value })} />}
      </label>)}
    </div>
    {!fields.topic.trim() && <p className="text-sm text-amber-700 dark:text-amber-300">{zh ? 'Vui lòng nhập chủ đề để tiếp tục' : 'Enter a topic to continue'}</p>}
    <div className="flex items-center justify-between gap-3 text-sm">
      <span>{zh ? 'Prompt Xem trước (có thể chỉnh sửa trực tiếp; Sau khi chỉnh sửa thủ công, Cập nhật trường sẽ không ghi đè bản xem trước) ' : 'Editable prompt preview (field changes preserve your manual edits)'}</span>
      <button type="button" className="text-blue-600 shrink-0" onClick={onRebuild}>{zh ? 'Cập nhật từ biểu mẫu Prompt' : 'Rebuild prompt from fields'}</button>
    </div>
  </fieldset>;
};