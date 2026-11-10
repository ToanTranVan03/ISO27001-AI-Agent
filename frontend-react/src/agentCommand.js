// Validation of Agent commands; independent of any scene or renderer.
export function agentSubmission(role,goal,mode,allowFallback,target) {
  if(!['coordination','inventory','security','report'].includes(role))throw new Error('Chọn vai trò Agent hợp lệ.');
  const text=goal.trim();
  if(text.length<8||text.length>600)throw new Error('Mục tiêu cần từ 8 đến 600 ký tự.');
  if(!['agent','workflow'].includes(mode))throw new Error('Chọn chế độ thực thi hợp lệ.');
  if(!target?.employee_id||!target?.asset_id)throw new Error('Chọn nhân viên và máy đã đồng bộ trước khi giao việc.');
  return {goal:text,scope:'all',mode,allow_fallback:mode==='agent'&&Boolean(allowFallback),requested_role:role,
    target:{employee_id:target.employee_id,asset_id:target.asset_id}};
}
