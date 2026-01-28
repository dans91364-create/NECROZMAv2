#!/usr/bin/env python3
"""
🐉 NECROZMAv2 - LIGHT REPORT

Strategy Report Generator (Text/CSV only, no HTML dashboard)
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class LightReport:
    """
    Generate text and CSV reports for strategy rankings.
    
    Usage:
        report = LightReport(output_dir="results/2026-01")
        report.generate_all(ranking, legendaries)
    """
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_ranking_csv(self, ranking: pd.DataFrame, filename: str = "ranking_all.csv"):
        """Save full ranking to CSV."""
        path = self.output_dir / filename
        ranking.to_csv(path, index=False)
        print(f"📊 Ranking saved: {path}")
        return path
    
    def save_legendaries_csv(self, legendaries: pd.DataFrame, filename: str = "ranking_top13.csv"):
        """Save top 13 legendaries to CSV."""
        path = self.output_dir / filename
        legendaries.to_csv(path, index=False)
        print(f"🏆 Legendaries saved: {path}")
        return path
    
    def save_summary_json(self, ranking: pd.DataFrame, legendaries: pd.DataFrame, 
                          filename: str = "summary_stats.json"):
        """Save summary statistics to JSON."""
        # Handle empty ranking
        if len(ranking) == 0:
            summary = {
                'generated_at': datetime.now().isoformat(),
                'total_strategies': 0,
                'total_positive': 0,
                'total_negative': 0,
                'pct_positive': 0.0,
                'legendaries': []
            }
        else:
            summary = {
                'generated_at': datetime.now().isoformat(),
                'total_strategies': len(ranking),
                'total_positive': int((ranking['total_return'] > 0).sum()),
                'total_negative': int((ranking['total_return'] < 0).sum()),
                'pct_positive': float((ranking['total_return'] > 0).sum() / len(ranking) * 100),
                'best_return': float(ranking['total_return'].max()),
                'worst_return': float(ranking['total_return'].min()),
                'avg_return': float(ranking['total_return'].mean()),
                'median_return': float(ranking['total_return'].median()),
                'avg_sharpe': float(ranking['sharpe_ratio'].mean()),
                'avg_sortino': float(ranking['sortino_ratio'].mean()),
                'avg_win_rate': float(ranking['win_rate'].mean()),
                'avg_max_drawdown': float(ranking['max_drawdown'].mean()),
                'legendaries': legendaries.to_dict('records')
            }
        
        path = self.output_dir / filename
        with open(path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"📋 Summary saved: {path}")
        return path
    
    def generate_text_report(self, ranking: pd.DataFrame, legendaries: pd.DataFrame,
                            filename: str = "light_report.txt") -> str:
        """Generate text report."""
        lines = []
        
        # Handle empty ranking
        if len(ranking) == 0:
            lines.append("=" * 80)
            lines.append("🐉 NECROZMAv2 - GRANDE TESTE REPORT")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("=" * 80)
            lines.append("\n⚠️  No strategies to report\n")
            lines.append("=" * 80)
            report_text = "\n".join(lines)
            path = self.output_dir / filename
            with open(path, 'w') as f:
                f.write(report_text)
            return report_text
        
        # Header
        lines.append("=" * 80)
        lines.append("🐉 NECROZMAv2 - GRANDE TESTE REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary stats
        lines.append("📊 SUMMARY STATISTICS")
        lines.append("-" * 40)
        lines.append(f"Total strategies tested: {len(ranking)}")
        lines.append(f"Profitable strategies: {(ranking['total_return'] > 0).sum()} ({(ranking['total_return'] > 0).sum() / len(ranking) * 100:.1f}%)")
        lines.append(f"Best return: {ranking['total_return'].max():.2f}%")
        lines.append(f"Worst return: {ranking['total_return'].min():.2f}%")
        lines.append(f"Average return: {ranking['total_return'].mean():.2f}%")
        lines.append(f"Average Sharpe: {ranking['sharpe_ratio'].mean():.3f}")
        lines.append(f"Average Win Rate: {ranking['win_rate'].mean():.1f}%")
        lines.append("")
        
        # Top 13 Legendaries
        lines.append("🏆 TOP 13 LENDÁRIOS")
        lines.append("-" * 80)
        lines.append(f"{'#':<3} {'Strategy':<25} {'Return':<10} {'Sharpe':<8} {'Sortino':<8} {'WinRate':<8} {'MaxDD':<8} {'Score':<8}")
        lines.append("-" * 80)
        
        for _, row in legendaries.iterrows():
            lines.append(
                f"{int(row['rank']):<3} "
                f"{row['strategy'][:24]:<25} "
                f"{row['total_return']:>8.2f}% "
                f"{row['sharpe_ratio']:>7.3f} "
                f"{row['sortino_ratio']:>7.3f} "
                f"{row['win_rate']:>6.1f}% "
                f"{row['max_drawdown']:>6.1f}% "
                f"{row['composite_score']:>7.4f}"
            )
        
        lines.append("-" * 80)
        lines.append("")
        
        # Footer
        lines.append("=" * 80)
        lines.append("🐉 NECROZMAv2 - \"288 strategies enter. 13 Legendaries emerge.\"")
        lines.append("=" * 80)
        
        report_text = "\n".join(lines)
        
        # Save to file
        path = self.output_dir / filename
        with open(path, 'w') as f:
            f.write(report_text)
        print(f"📄 Report saved: {path}")
        
        return report_text
    
    def generate_all(self, ranking: pd.DataFrame, legendaries: pd.DataFrame):
        """Generate all reports (CSV, JSON, TXT)."""
        self.save_ranking_csv(ranking)
        self.save_legendaries_csv(legendaries)
        self.save_summary_json(ranking, legendaries)
        report_text = self.generate_text_report(ranking, legendaries)
        
        # Also print to console
        print("\n" + report_text)
        
        return {
            'ranking_csv': self.output_dir / "ranking_all.csv",
            'legendaries_csv': self.output_dir / "ranking_top13.csv",
            'summary_json': self.output_dir / "summary_stats.json",
            'report_txt': self.output_dir / "light_report.txt"
        }
