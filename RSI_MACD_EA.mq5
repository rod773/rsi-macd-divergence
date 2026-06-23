//+------------------------------------------------------------------+
//| RSI_MACD_EA.mq5                                                  |
//| Trades regular/hidden MACD histogram divergences                 |
//+------------------------------------------------------------------+
#property copyright "RSI MACD Divergence"
#property version   "1.00"

#include <Trade\Trade.mqh>
CTrade Trade;

input group "=== MACD ==="
input int      FastMA     = 12;
input int      SlowMA     = 26;
input int      SignalEMA  = 9;

input group "=== Trade ==="
input double   LotSize    = 0.1;
input double   TP_Pct     = 0.004;
input double   SL_Pct     = 0.002;
input bool     UseHidden  = false;
input int      Magic      = 202406;

//+------------------------------------------------------------------+
double SMA(const double &a[], int start, int len) {
   double s = 0;
   for (int i = 0; i < len; i++) s += a[start + i];
   return s / len;
}
//+------------------------------------------------------------------+
bool Top(const double &h[], int c) {
   return h[c+2] < h[c] && h[c+1] < h[c] && h[c] > h[c-1] && h[c] > h[c-2];
}
bool Bot(const double &h[], int c) {
   return h[c+2] > h[c] && h[c+1] > h[c] && h[c] < h[c-1] && h[c] < h[c-2];
}
//+------------------------------------------------------------------+
bool HasPos(int t) {
   for (int i = PositionsTotal() - 1; i >= 0; i--)
      if (PositionGetTicket(i) > 0 && PositionSelectByTicket(PositionGetTicket(i)))
         if (PositionGetInteger(POSITION_MAGIC) == Magic &&
             PositionGetString(POSITION_SYMBOL) == _Symbol &&
             (int)PositionGetInteger(POSITION_TYPE) == t)
            return true;
   return false;
}
//+------------------------------------------------------------------+
void OnInit() {
   Trade.SetExpertMagicNumber(Magic);
}
//+------------------------------------------------------------------+
void OnTick() {
   static datetime lastBar = 0;
   datetime now = iTime(_Symbol, PERIOD_CURRENT, 0);
   if (now == lastBar) return;
   lastBar = now;

   int need = SlowMA + 10;
   if (Bars(_Symbol, PERIOD_CURRENT) < need) return;

   double c[], h[], l[];
   ArraySetAsSeries(c, true);
   ArraySetAsSeries(h, true);
   ArraySetAsSeries(l, true);
   if (CopyClose(_Symbol, PERIOD_CURRENT, 0, need, c) < need) return;
   if (CopyHigh( _Symbol, PERIOD_CURRENT, 0, need, h) < need) return;
   if (CopyLow(  _Symbol, PERIOD_CURRENT, 0, need, l) < need) return;

   // ---------- MACD (SMA fast/slow, EMA signal) ----------
   int n = need - SlowMA + 1;
   double macd[], sig[], hist[];
   ArrayResize(macd, n); ArrayResize(sig, n); ArrayResize(hist, n);
   for (int i = 0; i < n; i++)
      macd[i] = SMA(c, i, FastMA) - SMA(c, i, SlowMA);

   double k = 2.0 / (SignalEMA + 1);
   sig[n - 1] = macd[n - 1];
   for (int i = n - 2; i >= 0; i--)
      sig[i] = macd[i] * k + sig[i + 1] * (1 - k);
   for (int i = 0; i < n; i++)
      hist[i] = macd[i] - sig[i];

   // ---------- fractal & divergence scan (oldest→newest) ----------
   // Scans oldest-first so the last divergence found is the most recent.
   // Only signals from the last 5 bars (cIdx <= 6) are traded to avoid stale entries.
   int side = 0; // +1 long, -1 short
   int lastTopC = -1; double lastTopH = 0, lastTopP = 0;
   int lastBotC = -1; double lastBotH = 0, lastBotP = 0;

   for (int cIdx = n - 3; cIdx >= 2; cIdx--) {
      if (Top(hist, cIdx)) {
         if (lastTopC >= 0) {
            double ph = h[cIdx], phist = hist[cIdx];
            if      (ph > lastTopP && phist < lastTopH) side = -1;
            else if (ph < lastTopP && phist > lastTopH && UseHidden) side = -1;
         }
         lastTopC = cIdx; lastTopH = hist[cIdx]; lastTopP = h[cIdx];
      }
      if (Bot(hist, cIdx)) {
         if (lastBotC >= 0) {
            double pl = l[cIdx], phist = hist[cIdx];
            if      (pl < lastBotP && phist > lastBotH) side = 1;
            else if (pl > lastBotP && phist < lastBotH && UseHidden) side = 1;
         }
         lastBotC = cIdx; lastBotH = hist[cIdx]; lastBotP = l[cIdx];
      }
   }

   // ---------- trade (only fresh signals) ----------
   if (side == 1 && lastBotC >= 0 && lastBotC <= 6 && !HasPos(POSITION_TYPE_BUY)) {
      if (HasPos(POSITION_TYPE_SELL)) Trade.PositionClose(_Symbol, 3);
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      Trade.Buy(LotSize, _Symbol, ask, ask * (1 - SL_Pct), ask * (1 + TP_Pct), "RBD Long");
   }
   else if (side == -1 && lastTopC >= 0 && lastTopC <= 6 && !HasPos(POSITION_TYPE_SELL)) {
      if (HasPos(POSITION_TYPE_BUY)) Trade.PositionClose(_Symbol, 3);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      Trade.Sell(LotSize, _Symbol, bid, bid * (1 + SL_Pct), bid * (1 - TP_Pct), "RBD Short");
   }
}
//+------------------------------------------------------------------+
