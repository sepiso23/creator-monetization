import {
  DollarSign,
  ArrowUpRight,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

const Overview = ({ walletData }) => {
  const statCards = [
    {
      label: "Balance",
      val: walletData?.balance,
      icon: DollarSign,
      color: "text-zed-green",
      bg: "bg-green-50",
    },
    {
      label: "Outgoing",
      val: walletData?.totalOutgoing,
      icon: ArrowUpRight,
      color: "text-orange-600",
      bg: "bg-orange-50",
    },
    {
      label: "Supporters",
      val: walletData?.recentTransactions?.filter(t => t.type === 'DEPOSIT' && t.status === 'COMPLETED').length || 0,
      icon: Users,
      color: "text-blue-600",
      bg: "bg-blue-50",
      link: "/creator-dashboard/supporters"
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
      {statCards.map((stat, i) => {
        const CardContent = (
          <>
            <div
              className={`${stat.bg} ${stat.color} w-10 h-10 flex items-center justify-center rounded-xl mb-4`}
            >
              <stat.icon size={20} />
            </div>
            <p className="text-xs font-bold text-gray-400 uppercase">
              {stat.label}
            </p>
            <h3 className="text-2xl font-black text-gray-900">
              {stat.label === "Supporters" ? stat.val : `${walletData?.currency} ${Number(stat.val).toLocaleString()}`}
            </h3>
          </>
        );

        if (stat.link) {
          return (
            <Link
              key={i}
              to={stat.link}
              className="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm hover:shadow-md transition-shadow block"
            >
              {CardContent}
            </Link>
          );
        }

        return (
          <div
            key={i}
            className="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm"
          >
            {CardContent}
          </div>
        );
      })}
    </div>
  );
};

export default Overview;

