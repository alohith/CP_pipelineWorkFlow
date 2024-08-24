package durbin.cyto;

import durbin.stat.KolmogorovSmirnov;
import hep.aida.bin.StaticBin1D;
import hep.aida.ref.Histogram1D;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;

class DataUtils {
  public static String WellHeadingCol = "Well";

  public static String CompoundHeadingCol = "MoleculeID";

  public static String ConcentrationHeadingCol = "Concentration";

  public static String DataWellHeadingCol = "WellName";

  public static HashMap<String, StaticBin1D> computeFeatureBins(String paramString, Set<String> paramSet) throws Exception {
    HashMap<Object, Object> featureBins = new HashMap<Object, Object>();
    BufferedReader reader = new BufferedReader(new FileReader(paramString));
    String line = reader.readLine();
    String[] headings = line.split(",", -1);
    byte lineCount = 0;
    while ((line = reader.readLine()) != null) {
      String[] fields = str.split(",", -1);
      if (++lineCount % 10000 == 0)
        System.err.println("Preprocessing line " + lineCount);
      byte i = 0;
      for (String featureValue : fields) {
        String featureName = headings[i++];
        if (!skipColumns.contains(featureName) && featureValue.length() != 0 && featureValue != null && !featureValue.startsWith("\""))
          try {
            if (featureBins.keySet().contains(featureName)) {
              ((StaticBin1D)featureBins.get(featureName)).add(Double.parseDouble(featureValue));
            } else {
              StaticBin1D bin = new StaticBin1D();
              bin.add(Double.parseDouble(featureValue));
              featureBins.put(featureName, bin);
            }
          } catch (NumberFormatException numberFormatException) {}
      }
    }
    return (HashMap)featureBins;
  }

  public static HashMap<String, Histogram1D> getCpMByFeatureMap(String paramString, int paramInt, HashMap<String, StaticBin1D> paramHashMap, HashMap<String, String> paramHashMap1, HashMap<String, String> paramHashMap2, Set<String> paramSet, HashSet<String> paramHashSet) throws Exception {
    BufferedReader bufferedReader = new BufferedReader(new FileReader(paramString));
    String str = bufferedReader.readLine();
    String[] arrayOfString = str.split(",", -1);
    HashMap<String, Integer> hashMap = makeColMap(arrayOfString);
    int i = ((Integer)hashMap.get(DataWellHeadingCol)).intValue();
    HashMap<Object, Object> hashMap1 = new HashMap<Object, Object>();
    byte b = 0;
    while ((str = bufferedReader.readLine()) != null) {
      String[] arrayOfString1 = str.split(",", -1);
      if (++b % 10000 == 0)
        System.err.println("Processing line " + b);
      String str1 = arrayOfString1[i];
      if (str1.length() <= 2) {
        System.err.println("getCpMByFeatureMap ERROR:  Empty well name: " + str1);
        System.err.println("offending Line: " + str);
        return null;
      }
      str1 = str1.substring(1, str1.length() - 1);
      String str2 = paramHashMap1.get(str1);
      String str3 = "udef";
      if (str2 == null)
        str2 = "Blank";
      if (str2 == "Blank") {
        str3 = "0";
      } else {
        str3 = paramHashMap2.get(str1);
      }
      if (str3 == "")
        str3 = "0";
      String str4 = str2 + "_" + str3;
      paramHashSet.add(str4);
      byte b1 = -1;
      for (String str5 : arrayOfString1) {
        b1++;
        if (str5 != null && str5.length() != 0) {
          String str6 = arrayOfString[b1];
          if (!paramSet.contains(str6)) {
            String str7 = str4 + str6;
            if (hashMap1.containsKey(str7)) {
              Histogram1D histogram1D = (Histogram1D)hashMap1.get(str7);
              if (histogram1D == null) {
                System.err.println("cyto.DataUtils Error: hist null for " + str7);
              } else {
                histogram1D.fill(Double.parseDouble(str5));
              }
            } else {
              StaticBin1D staticBin1D = paramHashMap.get(str6);
              if (staticBin1D == null)
                System.err.println("featureBin is null for: " + str6);
              double d1 = ((StaticBin1D)paramHashMap.get(str6)).min();
              double d2 = ((StaticBin1D)paramHashMap.get(str6)).max();
              if (d1 == d2)
                d2 = d1 + 0.5D * d1;
              if (d1 == d2)
                d2 = d1 + 1.0D;
              Histogram1D histogram1D = new Histogram1D("$featureName $CpM", paramInt, d1, d2);
              if (histogram1D == null) {
                System.err.println("cyto.DataUtils Error: hist null for " + str7);
              } else {
                histogram1D.fill(Double.parseDouble(str5));
                hashMap1.put(str7, histogram1D);
              }
            }
          }
        }
      }
    }
    System.err.println("About to return");
    return (HashMap)hashMap1;
  }

  public static HashMap<String, Integer> makeColMap(String[] paramArrayOfString) {
    HashMap<Object, Object> hashMap = new HashMap<Object, Object>();
    for (byte b = 0; b < paramArrayOfString.length; b++) {
      String str = paramArrayOfString[b];
      hashMap.put(str, Integer.valueOf(b));
    }
    return (HashMap)hashMap;
  }

  public static double getStatisticForCpM(String paramString1, HashMap<String, Histogram1D> paramHashMap, String paramString2, int paramInt, double[] paramArrayOfdouble1, double[] paramArrayOfdouble2, String paramString3) {
    double d2;
    double d3;
    ArrayList arrayList = new ArrayList();
    String str = paramString1 + paramString2;
    Histogram1D histogram1D = paramHashMap.get(str);
    if (histogram1D == null) {
      System.err.println("ERROR: Null distribution at " + str);
      return Double.NaN;
    }
    double[] arrayOfDouble1 = new double[paramInt];
    for (byte b = 0; b < paramInt; b++)
      arrayOfDouble1[b] = histogram1D.binHeight(b);
    double[] arrayOfDouble2 = exponentialSmoothing(arrayOfDouble1, 0.25D);
    double[] arrayOfDouble3 = normalize(arrayOfDouble2);
    null = -1.0D;
    switch (Measures.value(paramString3)) {
      case meandiff:
        return meandiff(arrayOfDouble2, paramArrayOfdouble1);
      case ksdist:
        return KolmogorovSmirnov.signedDistance(arrayOfDouble2, paramArrayOfdouble1);
      case ksprob:
        return KolmogorovSmirnov.test(arrayOfDouble3, paramArrayOfdouble2);
      case histdiff:
        d2 = 1.0D;
        return histSquareDiff(arrayOfDouble3, paramArrayOfdouble2, d2);
      case logdiff:
        d3 = 1.0D;
        return histLogDiff(arrayOfDouble3, paramArrayOfdouble2, d3);
    }
    double d1 = -1.0D;
    System.err.println("ERROR: unknown measure type: $measureType");
    return d1;
  }

  public static double histLogDiff(double[] paramArrayOfdouble1, double[] paramArrayOfdouble2, double paramDouble) {
    double d = 0.0D;
    for (byte b = 0; b < paramArrayOfdouble2.length; b++) {
      double d1 = paramArrayOfdouble2[b] - paramArrayOfdouble1[b] * paramDouble;
      d1 = -2.0D * Math.log(d1) / Math.log(2.0D);
      d += d1;
    }
    return d;
  }

  public static double histSquareDiff(double[] paramArrayOfdouble1, double[] paramArrayOfdouble2, double paramDouble) {
    double d1 = 0.0D;
    double d2 = 0.0D;
    double d3 = 0.0D;
    for (byte b = 0; b < paramArrayOfdouble2.length; b++) {
      d2 += paramArrayOfdouble2[b] * b;
      d3 += paramArrayOfdouble1[b] * b;
      double d = paramArrayOfdouble2[b] - paramArrayOfdouble1[b] * paramDouble;
      d *= d;
      d1 += d;
    }
    if (d2 > d3)
      d1 = -d1;
    return d1;
  }

  public static double[] exponentialSmoothing(double[] paramArrayOfdouble, double paramDouble) {
    int i = paramArrayOfdouble.length;
    double[] arrayOfDouble = new double[i];
    arrayOfDouble[0] = paramArrayOfdouble[0] + paramDouble * (paramArrayOfdouble[1] - paramArrayOfdouble[0]);
    for (byte b = 1; b < i - 1; b++)
      arrayOfDouble[b] = paramDouble * (paramArrayOfdouble[b - 1] - paramArrayOfdouble[b]) + paramArrayOfdouble[b] + paramDouble * (paramArrayOfdouble[b + 1] - paramArrayOfdouble[b]);
    arrayOfDouble[i - 1] = paramDouble * (paramArrayOfdouble[i - 2] - paramArrayOfdouble[i - 1]) + paramArrayOfdouble[i - 1];
    return arrayOfDouble;
  }

  public static double[] normalize(double[] paramArrayOfdouble) {
    double d = 0.0D;
    for (byte b1 = 0; b1 < paramArrayOfdouble.length; b1++)
      d += paramArrayOfdouble[b1];
    double[] arrayOfDouble = new double[paramArrayOfdouble.length];
    for (byte b2 = 0; b2 < paramArrayOfdouble.length; b2++) {
      if (d == 0.0D) {
        arrayOfDouble[b2] = 0.0D;
      } else {
        arrayOfDouble[b2] = paramArrayOfdouble[b2] / d;
      }
    }
    return arrayOfDouble;
  }

  public static double meandiff(double[] paramArrayOfdouble1, double[] paramArrayOfdouble2) {
    double d1 = 0.0D;
    double d2 = 0.0D;
    for (byte b1 = 0; b1 < paramArrayOfdouble1.length; b1++) {
      d1 += paramArrayOfdouble1[b1];
      d2++;
    }
    double d3 = d1 / d2;
    double d4 = 0.0D;
    double d5 = 0.0D;
    for (byte b2 = 0; b2 < paramArrayOfdouble2.length; b2++) {
      d4 += paramArrayOfdouble2[b2];
      d5++;
    }
    double d6 = d4 / d5;
    double d7 = d3 - d6;
    double d8 = 1.0E-9D;
    if (d6 != 0.0D)
      d8 = d7 / d6;
    return d8;
  }

  public enum Measures {
    meandiff, ksdist, ksprob, ksscaled, histdiff, logdiff, NOVALUE;

    public static Measures value(String param1String) {
      try {
        return valueOf(param1String);
      } catch (Exception exception) {
        return NOVALUE;
      }
    }
  }
}


/* Location:              D:\Akshar\ScottLokeyLab\Scripts_AL\CP_pipelineWorkFlow\.groovy\lib\durbinlib.jar!\durbin\cyto\DataUtils.class
 * Java compiler version: 6 (50.0)
 * JD-Core Version:       1.1.3
 */
