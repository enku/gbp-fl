/* global Chart, machines, gradientColors, barBorderRadius */

function filesByMachineChart() {
  const machineFiles = JSON.parse(document.getElementById('machineFiles').textContent);
  const fileCounts = Array.from(machines, (machine) => machineFiles[machine].total);
  const filesByMachineConfig = {
    type: 'bar',
    responsive: true,
    data: {
      labels: machines,
      datasets: [
        {
          data: fileCounts,
          backgroundColor: gradientColors,
          borderRadius: barBorderRadius,
        },
      ],
    },
    options: {
      animations: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          ticks: {
            max: 30,
            stepSize: 1 * 10 ** 6,
            callback: (value) => `${value / 10 ** 6}M`,
          },
        },
      },
    },
  };
  const ctx = document.getElementById('filesByMachineChart');

  return new Chart(ctx, filesByMachineConfig);
}

document.addEventListener('DOMContentLoaded', () => filesByMachineChart());
