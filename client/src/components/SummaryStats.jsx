import React from 'react';
import { Card, CardContent } from './ui/card';
import { FiUsers, FiAlertCircle, FiCheckCircle, FiPercent } from 'react-icons/fi';
import { FaRupeeSign } from "react-icons/fa";

const StatCard = ({ title, value, icon: Icon, description }) => (
  <Card>
    <CardContent className="p-6">
      <div className="flex items-center space-x-4">
        <div className="p-2 bg-primary/10 rounded-full">
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <h3 className="text-2xl font-bold">{value}</h3>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      </div>
    </CardContent>
  </Card>
);

const formatNumber = (num) => {
  if (num === undefined || num === null) return '0';
  return new Intl.NumberFormat('en-US').format(num);
};

const formatCurrency = (num) => {
  if (num === undefined || num === null) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
};

const StatusRevenueCard = ({ title, statusRevenue, totalRevenue }) => {
  if (!statusRevenue || Object.keys(statusRevenue).length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">{title}</h3>
          <div className="text-center py-4 text-muted-foreground">
            No status-wise revenue data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Sort statuses by revenue (highest first)
  const sortedStatuses = Object.entries(statusRevenue)
    .sort(([, a], [, b]) => b - a);

  return (
    <Card>
      <CardContent className="pt-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <dl className="space-y-3">
          {sortedStatuses.map(([status, revenue]) => (
            <div key={status} className="flex justify-between items-center">
              <dt className="text-muted-foreground flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 bg-primary/70`}></div>
                {status}
              </dt>
              <dd className="font-medium">
                {formatCurrency(revenue)}
                <span className="text-xs text-muted-foreground ml-2">
                  ({Math.round((revenue / totalRevenue) * 100)}%)
                </span>
              </dd>
            </div>
          ))}
          <div className="flex justify-between items-center pt-2 border-t">
            <dt className="font-medium">Total Revenue</dt>
            <dd className="font-medium text-primary">{formatCurrency(totalRevenue)}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
};

const SummaryStats = ({ summaryData }) => {
  if (!summaryData) return null;

  const {
    total_records_file1 = 0,
    total_records_file2 = 0,
    matching_records_count = 0,
    mismatched_records_count = 0,
    duplicates_file1_count = 0,
    duplicates_file2_count = 0,
    only_in_file1_count = 0,
    only_in_file2_count = 0,
    total_revenue_file1 = 0,
    total_revenue_file2 = 0,
    status_revenue_file1 = {},
    status_revenue_file2 = {},
  } = summaryData;

  // Calculate match percentage
  const totalRecords = total_records_file1 + total_records_file2;
  const matchPercentage = totalRecords > 0 
    ? Math.round((matching_records_count / totalRecords) * 100) 
    : 0;

  return (
    <div className="space-y-8">
      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Records"
          value={formatNumber(total_records_file1 + total_records_file2)}
          icon={FiUsers}
          description={`File 1: ${formatNumber(total_records_file1)} | File 2: ${formatNumber(total_records_file2)}`}
        />
        
        <StatCard
          title="Matching Records"
          value={formatNumber(matching_records_count)}
          icon={FiCheckCircle}
          description={`${matchPercentage}% match rate`}
        />
        
        <StatCard
          title="Mismatched Records"
          value={formatNumber(mismatched_records_count)}
          icon={FiAlertCircle}
          description="Records with different values"
        />
        
        <StatCard
          title="Duplicate Records"
          value={formatNumber(duplicates_file1_count + duplicates_file2_count)}
          icon={FiAlertCircle}
          description={`File 1: ${formatNumber(duplicates_file1_count)} | File 2: ${formatNumber(duplicates_file2_count)}`}
        />
      </div>

      {/* Revenue Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Revenue (File 1)"
          value={formatCurrency(total_revenue_file1)}
          icon={FaRupeeSign}
        />
        
        <StatCard
          title="Total Revenue (File 2)"
          value={formatCurrency(total_revenue_file2)}
          icon={FaRupeeSign}
        />
        
        <StatCard
          title="Revenue Difference"
          value={formatCurrency(Math.abs(total_revenue_file1 - total_revenue_file2))}
          icon={FaRupeeSign}
          description={total_revenue_file1 > total_revenue_file2 ? "File 1 higher" : "File 2 higher"}
        />
        
        <StatCard
          title="Difference Percentage"
          value={`${total_revenue_file1 && total_revenue_file2 ? 
            Math.round(Math.abs(total_revenue_file1 - total_revenue_file2) / 
            ((total_revenue_file1 + total_revenue_file2) / 2) * 100) : 0}%`}
          icon={FiPercent}
        />
      </div>

      {/* Status-wise Revenue */}
      <div className="grid gap-6 md:grid-cols-2">
        <StatusRevenueCard 
          title="File 1 Status-wise Revenue" 
          statusRevenue={status_revenue_file1} 
          totalRevenue={total_revenue_file1} 
        />
        
        <StatusRevenueCard 
          title="File 2 Status-wise Revenue" 
          statusRevenue={status_revenue_file2} 
          totalRevenue={total_revenue_file2} 
        />
      </div>

      {/* Detailed Stats */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">File 1 Details</h3>
            <dl className="space-y-3">
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">Total Records</dt>
                <dd className="font-medium">{formatNumber(total_records_file1)}</dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">Unique Records</dt>
                <dd className="font-medium">{formatNumber(only_in_file1_count)}</dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">Duplicates</dt>
                <dd className="font-medium">{formatNumber(duplicates_file1_count)}</dd>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <dt className="text-muted-foreground">Total Revenue</dt>
                <dd className="font-medium text-primary">{formatCurrency(total_revenue_file1)}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">File 2 Details</h3>
            <dl className="space-y-3">
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">Total Records</dt>
                <dd className="font-medium">{formatNumber(total_records_file2)}</dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">Unique Records</dt>
                <dd className="font-medium">{formatNumber(only_in_file2_count)}</dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">Duplicates</dt>
                <dd className="font-medium">{formatNumber(duplicates_file2_count)}</dd>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <dt className="text-muted-foreground">Total Revenue</dt>
                <dd className="font-medium text-primary">{formatCurrency(total_revenue_file2)}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SummaryStats; 