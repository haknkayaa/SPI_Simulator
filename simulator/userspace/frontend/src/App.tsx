import { useState, useRef, useEffect } from 'react'
import { Button } from './components/ui/button'
import { Trash2, Download, Upload, Github, Terminal, Server, Monitor, Cpu, Copy, HelpCircle } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './components/ui/tooltip'
import toast, { Toaster } from 'react-hot-toast'

interface Command {
  id: number
  command: string
  response: string
  timestamp: string
}

interface Sequence {
  id: number
  received: string
  response: string
}

interface Log {
  id: number
  message: string
  timestamp: string
}

interface SystemStatus {
  backend: {
    status: boolean;
    port: number;
  };
  frontend: {
    status: boolean;
    port: number;
  };
  driver: {
    status: boolean;
    device: string;
  };
}

function App() {
  const [isRunning, setIsRunning] = useState(false)
  const [deviceExists, setDeviceExists] = useState(false)
  const [config, setConfig] = useState({
    device_path: '/dev/spidev0.0',
    bus_num: 0,
    cs_num: 0,
    speed: 1000000,
    mode: 0,
    bits_per_word: 8
  })
  const [command, setCommand] = useState('')
  const [commandList, setCommandList] = useState<Command[]>([])
  const [sequence, setSequence] = useState<Sequence[]>([])
  const [newReceived, setNewReceived] = useState('')
  const [newResponse, setNewResponse] = useState('')
  const [logList, setLogList] = useState<Log[]>([])
  const [lastLogId, setLastLogId] = useState<number>(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const terminalRef = useRef<HTMLDivElement>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    backend: { status: false, port: 5001 },
    frontend: { status: false, port: 5173 },
    driver: { status: false, device: '/dev/spidev0.0' }
  });
  const [previousStatus, setPreviousStatus] = useState<SystemStatus>({
    backend: { status: false, port: 5001 },
    frontend: { status: false, port: 5173 },
    driver: { status: false, device: '/dev/spidev0.0' }
  })
  const [quickResponse, setQuickResponse] = useState<string>('')
  const [showHowItWorks, setShowHowItWorks] = useState(false)

  const handleConfigChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({
      ...config,
      [field]: event.target.value
    })
  }

  const handleSaveConfig = async () => {
    try {
      // Extract device name from device path
      const deviceName = config.device_path.replace('/dev/', '');
      const requestBody = {
        device_name: deviceName,
        ...config
      };
      
      console.log('Sending config to backend:', requestBody);
      
      const response = await fetch('http://localhost:5001/api/spi/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })
      const data = await response.json()
      console.log('Config saved:', data)
    } catch (error) {
      console.error('Error saving config:', error)
    }
  }

  const handleSendCommand = async () => {
    if (!command.trim()) return

    try {
      const response = await fetch('http://localhost:5001/api/spi/quick-command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          command,
          device_path: config.device_path 
        }),
      })
      const data = await response.json()
      
      if (data.status === 'success') {
      const newCommand: Command = {
        id: Date.now(),
        command: command,
        response: data.response,
        timestamp: new Date().toLocaleTimeString()
      }
      
      setCommandList(prev => [...prev, newCommand])
        setQuickResponse(data.response)
      setCommand('')
      toast.success('Command sent successfully')
      } else {
        toast.error(data.message || 'Failed to send command')
      }
    } catch (error) {
      console.error('Error sending command:', error)
      toast.error('Failed to send command')
    }
  }

  const handleAddSequence = async () => {
    if (!newReceived.trim() || !newResponse.trim()) return

    const newSeq: Sequence = {
      id: Date.now(),
      received: newReceived,
      response: newResponse
    }

    try {
      // Send sequences to backend
      const response = await fetch('http://localhost:5001/api/spi/sequences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify([...sequence, newSeq]),
      })

      if (response.ok) {
        setSequence(prev => [...prev, newSeq])
        setNewReceived('')
        setNewResponse('')
        toast.success('Sequence added successfully')
      } else {
        console.error('Failed to save sequences')
        toast.error('Failed to save sequence')
      }
    } catch (error) {
      console.error('Error saving sequences:', error)
      toast.error('Failed to save sequence')
    }
  }

  const handleRemoveSequence = async (id: number) => {
    const newSequences = sequence.filter(seq => seq.id !== id)
    
    try {
      // Send updated sequences to backend
      const response = await fetch('http://localhost:5001/api/spi/sequences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSequences),
      })

      if (response.ok) {
        setSequence(newSequences)
        toast.success('Sequence removed successfully')
      } else {
        console.error('Failed to save sequences')
        toast.error('Failed to remove sequence')
      }
    } catch (error) {
      console.error('Error saving sequences:', error)
      toast.error('Failed to remove sequence')
    }
  }

  const toggleRunning = async () => {
    try {
      if (!isRunning) {
        // Driver'ı yükle
        const response = await fetch('http://localhost:5001/api/spi/load-driver', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            device_name: config.device_path.replace('/dev/', ''),
            sequences: sequence.map(seq => ({
              received: seq.received,
              response: seq.response
            }))
          }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          // Backend'den gelen hata mesajını kullan
          const errorMessage = data.message || `HTTP error! status: ${response.status}`;
          throw new Error(errorMessage);
        }
        
        if (data.status === 'success') {
          setIsRunning(true);
          toast.success('Driver started successfully')
        } else {
          // Backend'den gelen hata mesajını göster
          toast.error(data.message || 'Failed to start driver')
        }
      } else {
        // Driver'ı kaldır
        const response = await fetch('http://localhost:5001/api/spi/unload-driver', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          // Backend'den gelen hata mesajını kullan
          const errorMessage = data.message || `HTTP error! status: ${response.status}`;
          throw new Error(errorMessage);
        }
        
        if (data.status === 'success') {
          setIsRunning(false);
          toast.success('Driver stopped successfully')
        } else {
          // Backend'den gelen hata mesajını göster
          toast.error(data.message || 'Failed to stop driver')
        }
      }
    } catch (error) {
      console.error('Error toggling driver:', error);
      if (error instanceof Error) {
        // Backend'den gelen hata mesajını göster
        toast.error(error.message);
      } else {
        toast.error('Error toggling driver. Please make sure the backend is running.')
      }
      // Hata durumunda isRunning state'ini güncelleme
      setIsRunning(false);
    }
  };

  const handleExportSequences = () => {
    const dataStr = JSON.stringify(sequence, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `spi_sequences_${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const handleImportSequences = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const importedSequences = JSON.parse(e.target?.result as string)
        if (Array.isArray(importedSequences)) {
          setSequence(importedSequences)
        }
      } catch (error) {
        console.error('Error importing sequences:', error)
        alert('Invalid sequence file format')
      }
    }
    reader.readAsText(file)
  }

  const handleExportConfig = () => {
    const dataStr = JSON.stringify(config, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `spi_config_${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const handleImportConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const importedConfig = JSON.parse(e.target?.result as string)
        setConfig(importedConfig)
        toast.success('Configuration imported successfully')
      } catch (error) {
        console.error('Error importing configuration:', error)
        toast.error('Invalid configuration file format')
      }
    }
    reader.readAsText(file)
  }

  // Log'ları kontrol et
  const checkLogs = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/spi/logs');
      const data = await response.json();
      
      if (data.status === 'success') {
        const newLogs = data.logs.map((log: string, index: number) => ({
          id: Date.now() + index,
          message: log,
          timestamp: new Date().toLocaleTimeString()
        }));
        
        setLogList(newLogs);
      }
    } catch (error) {
      console.error('Error checking logs:', error);
    }
  };

  // Terminal'i temizle
  const clearTerminal = async () => {
    try {
      // Backend'deki logları temizle
      const response = await fetch('http://localhost:5001/api/spi/clear-logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to clear logs');
      }

      // Frontend'deki logları temizle
      setLogList([]);
      setLastLogId(0);
    } catch (error) {
      console.error('Error clearing logs:', error);
      toast.error('Failed to clear logs');
    }
  };

  // Periyodik olarak log'ları kontrol et
  useEffect(() => {
    const interval = setInterval(checkLogs, 1000);
    return () => clearInterval(interval);
  }, []);

  // Terminal'i en son satıra scroll et
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logList, commandList]); // logList veya commandList değiştiğinde scroll et

  // Check system status
  const checkSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/system/status');
      const data = await response.json();
      
      if (data.status === 'success') {
        const newStatus = data.data;
        setSystemStatus(newStatus);
        // Driver durumunu kontrol et ve isRunning state'ini güncelle
        if (!newStatus.driver.status && isRunning) {
          setIsRunning(false);
        }
      }
    } catch (error) {
      console.error('Error checking system status:', error);
    }
  };

  // Periodically check system status
  useEffect(() => {
    const interval = setInterval(checkSystemStatus, 2000);
    // Initial check
    checkSystemStatus();
    return () => clearInterval(interval);
  }, []);

  // Terminal içeriğini kopyala
  const copyTerminalContent = () => {
    const content = logList.map(log => log.message).join('\n');
    navigator.clipboard.writeText(content);
    toast.success('Terminal content copied to clipboard');
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Toaster 
        position="bottom-right"
        toastOptions={{
          duration: 5000,
          style: {
            background: '#333',
            color: '#fff',
            maxWidth: '500px',
            wordBreak: 'break-word',
            whiteSpace: 'pre-wrap',
            padding: '16px',
            borderRadius: '8px',
            fontSize: '14px',
            lineHeight: '1.5'
          },
        }}
        gutter={8}
        containerStyle={{
          bottom: 20,
          right: 20,
        }}
      />

      {/* Status Panel */}
      <div className="bg-white border-b border-border p-2">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowHowItWorks(true)}
              className="text-gray-700 hover:text-gray-900"
            >
              <HelpCircle className="h-5 w-5 mr-2" />
              How it Works?
            </Button>
            <div className="flex items-center gap-4">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-2">
                      <Server className={`h-4 w-4 ${systemStatus.backend.status ? 'text-green-500' : 'text-red-500'}`} />
                      <span className="text-xs text-gray-700">
                        Backend ({systemStatus.backend.port})
                      </span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Backend Server {systemStatus.backend.status ? 'is running' : 'is not running'}</p>
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-2">
                      <Monitor className={`h-4 w-4 ${systemStatus.frontend.status ? 'text-green-500' : 'text-red-500'}`} />
                      <span className="text-xs text-gray-700">
                        Frontend ({systemStatus.frontend.port})
                      </span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Frontend Server {systemStatus.frontend.status ? 'is running' : 'is not running'}</p>
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-2">
                      <Cpu className={`h-4 w-4 ${systemStatus.driver.status ? 'text-green-500' : 'text-red-500'}`} />
                      <span className="text-xs text-gray-700">
                        Driver ({systemStatus.driver.device})
                      </span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>SPI Driver {systemStatus.driver.status ? 'is loaded' : 'is not loaded'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>
      </div>

      {/* How it Works Dialog */}
      {showHowItWorks && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">How it Works?</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowHowItWorks(false)}
                className="text-gray-500 hover:text-gray-700 border border-gray-200 hover:border-gray-300 rounded-full w-8 h-8 flex items-center justify-center"
              >
                ✕
              </Button>
            </div>
            <div className="space-y-4 text-gray-600">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Virtual Kernel Driver</h3>
                <p className="mb-2">This simulator uses a custom Linux kernel module to create a virtual SPI device:</p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Creates a virtual SPI device (e.g., /dev/spidev0.0)</li>
                  <li>Implements standard SPI protocol in kernel space</li>
                  <li>Handles SPI transactions with configurable parameters</li>
                  <li>Provides real-time response simulation</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">1. Configuration</h3>
                <p>Set up your virtual SPI device parameters:</p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Device Path: Virtual device path (e.g., /dev/spidev0.0)</li>
                  <li>Bus Number: Virtual SPI bus number</li>
                  <li>CS (Chip Select): Virtual chip select number</li>
                  <li>Speed: SPI communication speed in Hz</li>
                  <li>Mode: SPI mode (0-3) for clock polarity and phase</li>
                  <li>Bits: Bits per word (typically 8)</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">2. Sequence Management</h3>
                <p>Define expected command-response pairs for the virtual device:</p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Add received data in hex format that the device should expect</li>
                  <li>Add corresponding response in hex format that the device should send</li>
                  <li>Manage multiple sequences for complex device behavior</li>
                  <li>Import/export sequences for different device configurations</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">3. Quick Actions</h3>
                <p>Test your virtual SPI device communication:</p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Send quick commands in hex format to the virtual device</li>
                  <li>View immediate responses from the device</li>
                  <li>Monitor communication in real-time</li>
                  <li>Test device behavior without physical hardware</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">4. Terminal</h3>
                <p>Monitor all SPI communication with the virtual device:</p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>View real-time logs of all SPI transactions</li>
                  <li>Track command history and responses</li>
                  <li>Copy terminal content for debugging</li>
                  <li>Clear logs when needed</li>
                </ul>
              </div>
              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="font-semibold text-gray-900 mb-2">Technical Details</h3>
                <p className="mb-2">The simulator works by:</p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Loading a custom kernel module that creates a virtual SPI device</li>
                  <li>Intercepting SPI transactions at the kernel level</li>
                  <li>Matching received commands against defined sequences</li>
                  <li>Generating appropriate responses based on the configuration</li>
                  <li>Providing a user-space interface for configuration and monitoring</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Title */}
      <div className="bg-black py-8">
        <div className="container mx-auto max-w-6xl">
          <h1 className="text-4xl md:text-5xl font-bold text-white text-center">
            Virtual SPI Simulator
          </h1>
          <p className="text-gray-400 text-center mt-2">
            A powerful tool for simulating and testing SPI communication
          </p>
        </div>
      </div>

      {/* Configuration Header */}
      <div className="bg-black border-b border-border p-4">
        <div className="container mx-auto max-w-6xl">
          <h1 className="text-2xl font-bold text-white mb-4">Virtual SPI Configuration</h1>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4 flex-1">
              <div className="flex-1">
                <label className="block text-xs font-medium mb-1 text-white">Device Path</label>
                <input
                  type="text"
                  value={config.device_path}
                  onChange={handleConfigChange('device_path')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-white">Bus</label>
                <input
                  type="number"
                  value={config.bus_num}
                  onChange={handleConfigChange('bus_num')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-white">CS</label>
                <input
                  type="number"
                  value={config.cs_num}
                  onChange={handleConfigChange('cs_num')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-32">
                <label className="block text-xs font-medium mb-1 text-white">Speed (Hz)</label>
                <input
                  type="number"
                  value={config.speed}
                  onChange={handleConfigChange('speed')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-white">Mode</label>
                <input
                  type="number"
                  value={config.mode}
                  onChange={handleConfigChange('mode')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-white">Bits</label>
                <input
                  type="number"
                  value={config.bits_per_word}
                  onChange={handleConfigChange('bits_per_word')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
            </div>

            <div className="flex items-end gap-2">
              <Button 
                onClick={toggleRunning}
                variant={isRunning ? "destructive" : "default"}
                size="default"
                className={`h-9 ${!isRunning ? 'bg-green-600 hover:bg-green-700' : ''}`}
              >
                {isRunning ? 'Stop' : 'Start'}
              </Button>
              {deviceExists && (
                <span className="text-xs text-green-500 ml-2">
                  Device Ready
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto max-w-6xl p-8 flex-grow">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sequence Management */}
          <div className="bg-card rounded-lg shadow-lg p-6 border border-border">
            <h2 className="text-2xl font-semibold mb-4 text-foreground">Sequence Management</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Received Data (Hex)</label>
                  <input
                    type="text"
                    value={newReceived}
                    onChange={(e) => setNewReceived(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background text-foreground font-mono"
                    placeholder="Enter received hex..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Response (Hex)</label>
                  <input
                    type="text"
                    value={newResponse}
                    onChange={(e) => setNewResponse(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background text-foreground font-mono"
                    placeholder="Enter response hex..."
                  />
                </div>
              </div>
              <Button onClick={handleAddSequence} className="w-full">
                Add Sequence
              </Button>

              {/* Sequence List */}
              <div className="mt-4">
                {/* Table Header */}
                <div className="grid grid-cols-[60px_1fr_1fr_60px] gap-2 mb-2 px-2">
                  <div className="text-xs font-medium text-muted-foreground">ID</div>
                  <div className="text-xs font-medium text-muted-foreground">Received Data</div>
                  <div className="text-xs font-medium text-muted-foreground">Response</div>
                  <div className="text-xs font-medium text-muted-foreground text-right">Action</div>
                </div>
                
                {/* Sequence Items */}
                <div className="space-y-2">
                  {sequence.map((seq, index) => (
                    <div key={seq.id} className="grid grid-cols-[60px_1fr_1fr_60px] gap-2 items-center p-2 bg-background/50 rounded-md">
                      <div className="text-sm text-muted-foreground">#{index + 1}</div>
                      <div className="font-mono text-sm text-green-400">{seq.received}</div>
                      <div className="font-mono text-sm text-blue-400">{seq.response}</div>
                      <div className="flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveSequence(seq.id)}
                          className="text-destructive hover:text-destructive/90"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Action Panel */}
          <div className="bg-card rounded-lg shadow-lg p-6 border border-border">
            <h2 className="text-2xl font-semibold mb-4 text-foreground">Quick Actions</h2>
            <div className="space-y-4">
              {/* Quick Send Command */}
              <div>
                <label className="block text-sm font-medium mb-1 text-foreground">Quick Send Command</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-md bg-background text-foreground font-mono"
                    placeholder="Enter hex command..."
                  />
                  <Button onClick={handleSendCommand}>
                    Send
                  </Button>
                </div>
                {quickResponse && (
                  <div className="mt-2 p-2 bg-background/50 rounded-md">
                    <div className="text-xs text-muted-foreground mb-1">Response:</div>
                    <div className="font-mono text-sm text-blue-400">{quickResponse}</div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleImportConfig}
                    className="hidden"
                    id="import-config"
                  />
                  <Button 
                    variant="outline"
                    size="default"
                    className="w-full text-foreground hover:text-foreground"
                    onClick={() => document.getElementById('import-config')?.click()}
                  >
                    Import Config
                  </Button>
                </div>
                <Button 
                  onClick={handleExportConfig}
                  variant="outline"
                  size="default"
                  className="w-full text-foreground hover:text-foreground"
                >
                  Export Config
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleImportSequences}
                    className="hidden"
                    id="import-sequences"
                  />
                  <Button 
                    variant="outline"
                    size="default"
                    className="w-full text-foreground hover:text-foreground"
                    onClick={() => document.getElementById('import-sequences')?.click()}
                  >
                    Import Sequences
                  </Button>
                </div>
                <Button 
                  onClick={handleExportSequences}
                  variant="outline"
                  size="default"
                  className="w-full text-foreground hover:text-foreground"
                >
                  Export Sequences
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Terminal (Command History) */}
        <div className="mt-6">
          <div className="bg-card rounded-lg shadow-lg p-6 border border-border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold text-foreground">Terminal</h2>
              <div className="flex gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={copyTerminalContent}
                        className="text-foreground hover:text-foreground"
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Copy terminal content</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearTerminal}
                  className="text-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              </div>
            </div>
            <div 
              ref={terminalRef}
              className="bg-black/50 rounded-md p-4 font-mono text-xs h-[300px] overflow-y-auto"
            >
              {logList.map((log) => (
                <div key={log.id}>
                  <div className="text-green-400">{log.message}</div>
                </div>
              ))}
              {commandList.map((cmd) => (
                <div key={cmd.id}>
                  <div className="text-gray-400 text-[10px]">{cmd.timestamp}</div>
                  <div className="text-green-400">&gt; {cmd.command}</div>
                  <div className="text-green-400">&lt; {cmd.response}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-card border-t border-border py-4">
        <div className="container mx-auto max-w-6xl px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="h-5 w-5 text-primary" />
              <span className="text-sm text-muted-foreground">
                Linux SPI Simulator v0.1.0 (Beta)
              </span>
            </div>
            
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/haknkayaa/SPI_Simulator"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="h-5 w-5" />
              </a>
              <span className="text-sm text-muted-foreground">
                © 2024
              </span>
            </div>
          </div>
          <div className="flex justify-center mt-2">
            <span className="text-sm text-muted-foreground">
              developed by{' '}
              <a
                href="https://hakankaya.kim/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80 transition-colors"
              >
                Hakan Kaya
              </a>
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App 