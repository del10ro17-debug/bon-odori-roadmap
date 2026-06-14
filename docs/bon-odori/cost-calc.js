/**
 * 晴海盆踊り2026 — 原価・売上シミュレーション計算
 * data.js の menu / salesSimulation と併用
 */
(function (global) {
  const parseQty = (qty) => {
    const m = String(qty).match(/([\d.]+)\s*(\D*)/);
    if (!m) return { amount: 1, unit: "個" };
    return { amount: parseFloat(m[1]), unit: m[2] || "個" };
  };

  const sumKebabCogs = (breakdown) =>
    (breakdown || []).reduce((sum, row) => sum + (Number(row.cost) || 0), 0);

  const solveUnitsForRevenue = (target, kebabSharePct, kebabPrice, drinkPrice) => {
    const targetNum = Math.max(0, Number(target) || 0);
    const share = Math.min(100, Math.max(0, Number(kebabSharePct) || 0)) / 100;
    const pk = Number(kebabPrice) || 700;
    const pd = Number(drinkPrice) || 300;
    if (targetNum === 0 || pk <= 0 || pd <= 0) {
      return { kebabUnits: 0, drinkUnits: 0, revenue: 0, gap: 0, kebabRevenueTarget: 0, drinkRevenueTarget: 0 };
    }

    const kebabRevenueTarget = targetNum * share;
    const drinkRevenueTarget = targetNum * (1 - share);
    const kebabUnits = Math.round(kebabRevenueTarget / pk);
    const drinkUnits = Math.round(drinkRevenueTarget / pd);
    const revenue = kebabUnits * pk + drinkUnits * pd;

    return {
      kebabUnits,
      drinkUnits,
      revenue,
      gap: Math.abs(revenue - targetNum),
      kebabRevenueTarget,
      drinkRevenueTarget,
    };
  };

  const calcProcurement = ({
    kebabUnits,
    drinkUnits,
    breakdown,
    kebabUnitCost,
    drinkUnitCost,
    bufferRate,
    eventDays,
    kebabPrice = 700,
    drinkPrice = 300,
  }) => {
    const k = Math.max(0, Number(kebabUnits) || 0);
    const d = Math.max(0, Number(drinkUnits) || 0);
    const unitCost = Number(kebabUnitCost) || 0;
    const drinkCost = Number(drinkUnitCost) || 0;
    const buffer = 1 + (Number(bufferRate) || 0);
    const days = Math.max(1, Number(eventDays) || 2);

    const ingredients = (breakdown || []).map((row) => {
      const spec = parseQty(row.qty);
      const need = k * spec.amount;
      return {
        item: row.item,
        qtyLabel: row.qty,
        unit: spec.unit,
        unitCost: Number(row.cost) || 0,
        need,
        buffered: need * buffer,
        lineCost: k * (Number(row.cost) || 0),
      };
    });

    const kebabFoodCost = k * unitCost;
    const drinkFoodCost = d * drinkCost;
    const totalCost = kebabFoodCost + drinkFoodCost;
    const kp = Number(kebabPrice) || 700;
    const dp = Number(drinkPrice) || 300;
    const kebabRevenue = k * kp;
    const drinkRevenue = d * dp;
    const revenue = kebabRevenue + drinkRevenue;

    return {
      kebabUnits: k,
      drinkUnits: d,
      revenue,
      kebabRevenue,
      drinkRevenue,
      kebabFoodCost,
      drinkFoodCost,
      totalCost,
      grossProfit: revenue - totalCost,
      grossMarginPct: revenue > 0 ? ((revenue - totalCost) / revenue) * 100 : 0,
      ingredients,
      drinkBuffered: Math.ceil(d * buffer),
      perDayKebab: k / days,
      perDayDrink: d / days,
      kebabUnitCost: unitCost,
    };
  };

  global.BonOdoriCostCalc = {
    parseQty,
    sumKebabCogs,
    solveUnitsForRevenue,
    calcProcurement,
  };
})(typeof window !== "undefined" ? window : globalThis);
