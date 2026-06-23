//+------------------------------------------------------------------+
//| RSI_MACD_Divergence_Indicator.mq5                                |
//| Replicates the Pine Script [RS]MACD Divergence V0                |
//+------------------------------------------------------------------+
#property copyright "RSI MACD Divergence"
#property version   "1.00"
#property indicator_separate_window
#property indicator_buffers 8
#property indicator_plots   7

// ---- MACD line ----
#property indicator_label1  "MACD"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrGray
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1

// ---- Signal line ----
#property indicator_label2  "SIGNAL"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrSilver
#property indicator_style2  STYLE_SOLID
#property indicator_width2  1

// ---- Histogram ----
#property indicator_label3  "HIST"
#property indicator_type3   DRAW_COLOR_HISTOGRAM
#property indicator_color3  clrBlack, clrMaroon, clrGreen

// ---- Top fractals (▼) ----
#property indicator_label4  "H F"
#property indicator_type4   DRAW_ARROW
#property indicator_color4  clrBlack

// ---- Bottom fractals (▲) ----
#property indicator_label5  "L F"
#property indicator_type5   DRAW_ARROW
#property indicator_color5  clrBlack

// ---- Bearish divergence (●) ----
#property indicator_label6  "H D"
#property indicator_type6   DRAW_ARROW
#property indicator_color6  clrMaroon

// ---- Bullish divergence (●) ----
#property indicator_label7  "L D"
#property indicator_type7   DRAW_ARROW
#property indicator_color7  clrGreen

input group "=== MACD ==="
input int FastMA    = 12;
input int SlowMA    = 26;
input int SignalEMA = 9;

double macdBuf[];
double sigBuf[];
double histBuf[];
int    histClr[];
double topBuf[];
double botBuf[];
double bearBuf[];
double bullBuf[];

//+------------------------------------------------------------------+
void OnInit() {
   SetIndexBuffer(0, macdBuf,  INDICATOR_DATA);
   SetIndexBuffer(1, sigBuf,   INDICATOR_DATA);
   SetIndexBuffer(2, histBuf,  INDICATOR_DATA);
   SetIndexBuffer(3, histClr,  INDICATOR_COLOR_INDEX);
   SetIndexBuffer(4, topBuf,   INDICATOR_DATA);
   SetIndexBuffer(5, botBuf,   INDICATOR_DATA);
   SetIndexBuffer(6, bearBuf,  INDICATOR_DATA);
   SetIndexBuffer(7, bullBuf,  INDICATOR_DATA);

   // histogram colour indexes: 0=neutral, 1=negative(maroon), 2=positive(green)
   PlotIndexSetInteger(2, PLOT_COLOR_INDEXES, 3);
   PlotIndexSetInteger(2, PLOT_LINE_COLOR, 0, clrBlack);
   PlotIndexSetInteger(2, PLOT_LINE_COLOR, 1, clrMaroon);
   PlotIndexSetInteger(2, PLOT_LINE_COLOR, 2, clrGreen);

   // fractal markers (placed directly at centre bar, no shift needed)
   PlotIndexSetInteger(3, PLOT_ARROW, 118);    // ▼
   PlotIndexSetInteger(4, PLOT_ARROW, 117);    // ▲

   // divergence markers
   PlotIndexSetInteger(5, PLOT_ARROW, 108);    // ●
   PlotIndexSetInteger(5, PLOT_LINE_WIDTH, 3);
   PlotIndexSetInteger(6, PLOT_ARROW, 108);    // ●
   PlotIndexSetInteger(6, PLOT_LINE_WIDTH, 3);

   IndicatorSetString(INDICATOR_SHORTNAME,
      "RSI MACD Div(" + IntegerToString(FastMA) + "," +
      IntegerToString(SlowMA) + "," + IntegerToString(SignalEMA) + ")");
}
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[]) {
   if (rates_total < SlowMA + 5) return 0;

   // ---- MACD (SMA fast, SMA slow) ----
   for (int i = prev_calculated > 0 ? prev_calculated - 1 : SlowMA; i < rates_total; i++) {
      double sf = 0, ss = 0;
      for (int j = 0; j < FastMA; j++) sf += close[i - j];
      for (int j = 0; j < SlowMA; j++) ss += close[i - j];
      macdBuf[i] = sf / FastMA - ss / SlowMA;
   }

   // ---- EMA signal ----
   double k = 2.0 / (SignalEMA + 1);
   if (prev_calculated == 0)
      sigBuf[SlowMA] = macdBuf[SlowMA];
   int sStart = prev_calculated > 0 ? prev_calculated - 1 : SlowMA + 1;
   for (int i = sStart; i < rates_total; i++)
      sigBuf[i] = macdBuf[i] * k + sigBuf[i - 1] * (1 - k);

   // ---- histogram ----
   int hStart = prev_calculated > 0 ? prev_calculated - 1 : SlowMA + 1;
   for (int i = hStart; i < rates_total; i++) {
      histBuf[i] = macdBuf[i] - sigBuf[i];
      histClr[i] = histBuf[i] >= 0 ? 2 : 1;
   }

   // ---- fractal + divergence (oldest→newest scan) ----
   if (prev_calculated == 0) {
      ArrayInitialize(topBuf,  EMPTY_VALUE);
      ArrayInitialize(botBuf,  EMPTY_VALUE);
      ArrayInitialize(bearBuf, EMPTY_VALUE);
      ArrayInitialize(bullBuf, EMPTY_VALUE);
   }

   int lastTop = -1; double ltv = 0, ltp = 0;
   int lastBot = -1; double lbv = 0, lbp = 0;

   for (int i = 2; i < rates_total - 2; i++) {
      bool top = histBuf[i] > histBuf[i-1] && histBuf[i] > histBuf[i+1] &&
                 histBuf[i] > histBuf[i-2] && histBuf[i] > histBuf[i+2];
      bool bot = histBuf[i] < histBuf[i-1] && histBuf[i] < histBuf[i+1] &&
                 histBuf[i] < histBuf[i-2] && histBuf[i] < histBuf[i+2];

      // reset current bar's divergence markers (they may be overwritten below)
      bearBuf[i] = EMPTY_VALUE;
      bullBuf[i] = EMPTY_VALUE;

      if (top) {
         topBuf[i] = histBuf[i];
         if (lastTop >= 0) {
            if      (high[i] > ltp && histBuf[i] < ltv) bearBuf[i] = histBuf[i]; // regular bear
            else if (high[i] < ltp && histBuf[i] > ltv) bearBuf[i] = histBuf[i]; // hidden bear
         }
         lastTop = i; ltv = histBuf[i]; ltp = high[i];
      }

      if (bot) {
         botBuf[i] = histBuf[i];
         if (lastBot >= 0) {
            if      (low[i] < lbp && histBuf[i] > lbv) bullBuf[i] = histBuf[i]; // regular bull
            else if (low[i] > lbp && histBuf[i] < lbv) bullBuf[i] = histBuf[i]; // hidden bull
         }
         lastBot = i; lbv = histBuf[i]; lbp = low[i];
      }
   }

   return rates_total;
}
//+------------------------------------------------------------------+
