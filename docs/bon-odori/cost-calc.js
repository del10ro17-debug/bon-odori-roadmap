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
    if (targetNum === 0) return { kebabUnits: 0, drinkUnits: 0, revenue: 0, gap: 0 };

    const kCenter = Math.round((targetNum * share) / pk);
    let best = { kebabUnits: 0, drinkUnits: 0, revenue: 0, gap: targetNum };

    for (let k = Math.max(0, kCenter - 80); k <= kCenter + 80; k += 1) {
      const remaining = targetNum - k * pk;
      if (remaining < 0) continue;
      const d = Math.round(remaining / pd);
      const revenue = k * pk + d * pd;
      const gap = Math.abs(revenue - targetNum);
      if (gap < best.gap) best = { kebabUnits: k, drinkUnits: d, revenue, gap };
    }
    return best;
  };

  const calcProcurement = ({
    kebabUnits,
    drinkUnits,
    breakdown,
    kebabUnitCost,
    drinkUnitCost,
    bufferRate,
    eventDays,
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
    const kebabRevenue = k * 700;
    const drinkRevenue = d * 300;
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
